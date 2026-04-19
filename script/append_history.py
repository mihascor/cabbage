import sqlite3
from contextlib import closing
from datetime import datetime

DB_PATH = r"C:\cabbage\data\cabbagedb.db"

# Добавление данных в историю open_interest_history из open_interest_record с UPSERT (вставка или обновление)
def append_history():
    today = datetime.now().strftime("%Y-%m-%d")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        try:
            with closing(conn.cursor()) as cursor:

                # 1. Читаем текущие данные
                cursor.execute("""
                    SELECT
                        name,
                        private_long,
                        private_shorts,
                        legal_long,
                        legal_shorts
                    FROM open_interest_record
                """)

                rows = cursor.fetchall()

                if not rows:
                    print("Нет данных в open_interest_record")
                    return

                # 2. Подготовка данных
                data = [
                    (
                        r[0],      # name
                        today,     # date
                        r[1],
                        r[2],
                        r[3],
                        r[4],
                    )
                    for r in rows
                ]

                # 3. UPSERT (вставка или обновление)
                cursor.executemany("""
                    INSERT INTO open_interest_history (
                        name,
                        date,
                        private_long,
                        private_shorts,
                        legal_long,
                        legal_shorts
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name, date) DO UPDATE SET
                        private_long = excluded.private_long,
                        private_shorts = excluded.private_shorts,
                        legal_long = excluded.legal_long,
                        legal_shorts = excluded.legal_shorts
                """, data)

            conn.commit()
            print(f"Обработано {len(data)} строк (insert/update)")

        except Exception as e:
            conn.rollback()
            print("Ошибка:", e)
            raise


if __name__ == "__main__":
    append_history()