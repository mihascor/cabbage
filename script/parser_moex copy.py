import asyncio
import logging
import sqlite3
import os
from contextlib import closing
from typing import List, Dict, Any, Optional, Callable
from script.append_history import append_history

from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = r"C:\Users\PC\AppData\Local\ms-playwright"

# --- CONFIG ---
DB_PATH = r"C:\cabbage\data\cabbagedb.db"
LOG_PATH = r"C:\cabbage\logs\parser_moex.log"
BASE_URL = "https://www.moex.com/ru/contract.aspx?code="

MAX_CONCURRENT = 5

PAGE_TIMEOUT_MS = 30000
WAIT_AFTER_LOAD_MS = 3000


# --- LOGGING ---
def setup_logging():
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
    )


# --- HELPERS ---
def normalize_period(period: Optional[str]) -> str:
    if period is None:
        return ""
    return str(period).strip()


def build_code(name: str, period: Optional[str]) -> str:
    name = str(name).strip()
    period = normalize_period(period)
    return name if period == "" else f"{name}{period}"


def parse_int(value: str) -> int:
    if value is None:
        raise ValueError("Пустое значение")

    cleaned = str(value).replace("\xa0", "").replace(" ", "").strip()

    if not cleaned:
        raise ValueError("Пустое числовое значение")

    return int(cleaned)


# --- DB ---
def fetch_futures_list() -> List[Dict[str, str]]:
    query = """
        SELECT name, period_name
        FROM futures_list
        ORDER BY rowid
    """

    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [{"name": r["name"], "period": r["period_name"]} for r in rows]


def save_open_interest(records: List[Dict[str, Any]]) -> None:
    query = """
        INSERT INTO open_interest_record (
            name, period,
            private_long, private_shorts,
            legal_long, legal_shorts
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    with closing(sqlite3.connect(DB_PATH)) as conn:
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute("DELETE FROM open_interest_record")

                data = [
                    (
                        r["name"],
                        r["period"],
                        r["private_long"],
                        r["private_shorts"],
                        r["legal_long"],
                        r["legal_shorts"],
                    )
                    for r in records
                ]

                cursor.executemany(query, data)

            conn.commit()
        except Exception:
            conn.rollback()
            raise


# --- PARSING ---
async def extract_data(page, url: str) -> Dict[str, int]:
    await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
    await page.wait_for_timeout(WAIT_AFTER_LOAD_MS)

    row_xpath = (
        "//table[contains(@class,'contract-open-positions')]"
        "//tr[td[contains(.,'Открытые позиции')]]"
    )

    await page.locator(f"xpath={row_xpath}").first.wait_for(timeout=PAGE_TIMEOUT_MS)

    async def get_td(n: int):
        return await page.locator(f"xpath={row_xpath}/td[{n}]").first.text_content()
    """
    Get the text content of the nth td element in the row.

    Args:
        n (int): The index of the td element to get.

    Returns:
        str: The text content of the nth td element.
    """

    return {
        "private_long": parse_int(await get_td(2)),
        "private_shorts": parse_int(await get_td(3)),
        "legal_long": parse_int(await get_td(4)),
        "legal_shorts": parse_int(await get_td(5)),
    }


# --- MAIN ---
async def main_async(log_callback: Callable[[str], None]):
    setup_logging()
    logging.info("Старт parser_moex_async")

    futures = fetch_futures_list()
    total = len(futures)

    if total == 0:
        log_callback("Таблица futures_list пуста")
        return

    log_callback(f"Всего инструментов: {total}")

    results: List[Optional[Dict[str, Any]]] = [None] * total
    errors = []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        stop_event = asyncio.Event()
        async def worker(index: int, item: Dict[str, str]):
            if stop_event.is_set():
                return
            async with semaphore:
                page = await browser.new_page()

                name = str(item["name"]).strip()
                period = normalize_period(item["period"])
                code = build_code(name, period)
                url = f"{BASE_URL}{code}"

                try:
                    data = await extract_data(page, url)

                    log_callback(f"{code} Ok {index+1}/{total}")

                    results[index] = {
                        "name": name,
                        "period": period,
                        **data,
                    }

                except Exception as e:
                    msg = f"{code} Error {index+1}/{total} ({e})"
                    log_callback(msg)
                    logging.error(msg)
                    stop_event.set()
                    raise

                finally:
                    await page.close()

        tasks = [worker(i, item) for i, item in enumerate(futures)]

        try:
            await asyncio.gather(*tasks)
        except Exception:
            log_callback("Критическая ошибка — остановка парсера")
            logging.error("Прервано из-за ошибки")
            await browser.close()
            return

        await browser.close()

    if errors or any(r is None for r in results):
        log_callback("Ошибка: не все данные получены. Запись в БД отменена.")
        logging.error("Отмена записи — есть ошибки")
        return

    save_open_interest(results)

    log_callback(f"Готово. Записано {len(results)} строк.")
    logging.info("Успешно записано %s строк", len(results))

    # --- добавляем запись в историю ---
    try:
        append_history()
        log_callback("История обновлена")
        logging.info("История успешно обновлена")
    except Exception as e:
        log_callback(f"Ошибка записи истории: {e}")
        logging.error("Ошибка append_history: %s", e)


def main(log_callback: Callable[[str], None] = print):
    asyncio.run(main_async(log_callback))


if __name__ == "__main__":
    main()