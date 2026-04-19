from datetime import datetime, timedelta
import json
import os
import sqlite3
import logging
import requests
from typing import List, Tuple

DB_PATH = r"C:\cabbage\data\cabbagedb.db"
STATE_FILE = r"C:\cabbage\data\last_price_update.json"


# -------------------------------
# Работа с файлом состояния
# -------------------------------
def get_last_update_date():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("last_update")


def set_last_update_date(date_str: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": date_str}, f, ensure_ascii=False, indent=4)


def need_update() -> bool:
    last_update = get_last_update_date()
    today_str = datetime.now().strftime("%Y-%m-%d")
    return last_update != today_str


# -------------------------------
# Получение истории цен с MOEX
# -------------------------------
def fetch_price_history(paper: str, is_stock: bool) -> List[Tuple[str, float, float]]:
    """
    MOEX ISS API:
    - акции: /stock/markets/shares
    - фьючерсы: /futures/markets/forts

    Возвращает список (date, high, low)
    только за последние 100 дней, исключая сегодня
    """

    # --- выбираем endpoint ---
    if is_stock:
        url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{paper}.json"
    else:
        url = f"https://iss.moex.com/iss/history/engines/futures/markets/forts/securities/{paper}.json"

    end_date = datetime.now().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=100)

    params = {
        "iss.meta": "off",
        "history.columns": "TRADEDATE,HIGH,LOW",
        "from": start_date.strftime("%Y-%m-%d"),
        "till": end_date.strftime("%Y-%m-%d")
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG RAW MOEX {paper}: keys =", data.keys())
        print(f"DEBUG RAW SAMPLE {paper}:", data.get("history", {}).get("data", [])[:2])

        rows = data.get("history", {}).get("data", [])

        # --- диапазон дат: 100 дней назад до вчера ---
        end_date = datetime.now().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=100)

        result = []

        for row in rows:
            trade_date = datetime.strptime(row[0], "%Y-%m-%d").date()

            if start_date <= trade_date <= end_date:
                high = row[1]
                low = row[2]

                result.append((
                    trade_date.strftime("%Y-%m-%d"),
                    float(high) if high is not None else None,
                    float(low) if low is not None else None
                ))

        return result

    except Exception as e:
        logging.exception(f"MOEX API error for {paper}: {e}")
        return []


# -------------------------------
# Основной сервис обновления
# -------------------------------
def run_update():
    print("=== Обновление price_history начато ===")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # --- получаем список инструментов ---
        cursor.execute("""
            SELECT paper, period_name
            FROM futures_list
        """)
        instruments = cursor.fetchall()

        print(f"Найдено инструментов: {len(instruments)}")

        for paper, period_name in instruments:
            try:
                is_stock = bool(period_name and period_name.strip())

                if is_stock:
                    print(f"[АКЦИЯ] {paper}")
                else:
                    print(f"[ФЬЮЧЕРС] {paper}")

                # --- получаем историю цен ---
                history = fetch_price_history(paper, is_stock)
                print(f"DEBUG {paper} history size = {len(history)}")
                print(f"DEBUG {paper} sample = {history[:2]}")

                # --- запись в БД ---
                for date_str, high, low in history:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO price_history (paper, date, high, low)
                            VALUES (?, ?, ?, ?)
                        """, (paper, date_str, high, low))
                    except Exception as e:
                        logging.exception(f"Ошибка записи строки {paper} {date_str} | {e}")
                        print(f"INSERT ERROR {paper} {date_str}: {e}")
                        continue

                conn.commit()

            except Exception:
                logging.exception(f"Ошибка обработки инструмента {paper}")
                continue

        # --- чистим старые данные (старше 100 дней) ---
        cutoff_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

        cursor.execute("""
            DELETE FROM price_history
            WHERE date < ?
        """, (cutoff_date,))

        conn.commit()
        conn.close()

        # фиксируем успешное обновление
        today_str = datetime.now().strftime("%Y-%m-%d")
        set_last_update_date(today_str)

        print("=== Обновление price_history завершено ===")

    except Exception:
        logging.exception("Критическая ошибка run_update()")