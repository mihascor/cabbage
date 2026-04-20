# SQL и подготовка данных для графиков ОИ и цены.
import sqlite3
from typing import List, Tuple

DB_PATH = r"C:\cabbage\data\cabbagedb.db"


# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНОЕ: получить paper по name через futures_list
# ------------------------------------------------------------
def _get_paper_by_name(name: str, conn: sqlite3.Connection) -> str:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT paper
        FROM futures_list
        WHERE name = ?
        LIMIT 1
        """,
        (name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


# ------------------------------------------------------------
# ДАННЫЕ ДЛЯ ГРАФИКА ЦЕНЫ
# Возвращает: List[(date, high, low)]
# ------------------------------------------------------------
def get_price_history(name: str) -> List[Tuple[str, float, float]]:
    with sqlite3.connect(DB_PATH) as conn:
        paper = _get_paper_by_name(name, conn)
        if not paper:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date, high, low
            FROM price_history
            WHERE paper = ?
            ORDER BY date
            """,
            (paper,)
        )

        rows = cursor.fetchall()

        result = []
        for date, high, low in rows:
            try:
                result.append((date, float(high), float(low)))
            except Exception:
                continue

        return result


# ------------------------------------------------------------
# ДАННЫЕ ДЛЯ ГРАФИКА ОИ
# Возвращает: List[(date, coef_fl, coef_ul)]
# ------------------------------------------------------------
def get_oi_history(name: str) -> List[Tuple[str, float, float]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                date,
                private_long,
                private_shorts,
                legal_long,
                legal_shorts
            FROM open_interest_history
            WHERE name = ?
            ORDER BY date
            """,
            (name,)
        )

        rows = cursor.fetchall()

        result = []

        for row in rows:
            date, pl, ps, ll, ls = row

            try:
                private_long = float(pl)
                private_shorts = float(ps)
                legal_long = float(ll)
                legal_shorts = float(ls)

                # --- расчёт коэффициентов ---
                max_fl = max(private_long, private_shorts)
                min_fl = min(private_long, private_shorts)
                coef_fl = round(max_fl / min_fl, 1) if min_fl != 0 else max_fl

                max_ul = max(legal_long, legal_shorts)
                min_ul = min(legal_long, legal_shorts)
                coef_ul = round(max_ul / min_ul, 1) if min_ul != 0 else max_ul

                # --- ограничение 20 ---
                coef_fl = min(coef_fl, 20)
                coef_ul = min(coef_ul, 20)

                # --- знак ---
                if private_long < private_shorts:
                    coef_fl *= -1

                if legal_long < legal_shorts:
                    coef_ul *= -1

                result.append((date, coef_fl, coef_ul))

            except Exception:
                continue

        return result