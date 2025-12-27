import sqlite3
import config

class DatabaseManager:
    def __init__(self):
        self.init_db()

    def _get_conn(self):
        return sqlite3.connect(config.DB_PATH)

    def init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ticks (timestamp REAL, price REAL)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_ts ON ticks (timestamp)''')
        conn.commit()
        conn.close()
        print(f"📦 [Database] 初始化完成: {config.DB_PATH}")

    def save_bulk_data(self, data_list):
        """
        批量写入数据，使用事务加速。
        data_list: list of [timestamp, price]
        """
        if not data_list: return 0
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute("BEGIN TRANSACTION")
            c.executemany("INSERT INTO ticks VALUES (?, ?)", data_list)
            c.execute("COMMIT")
            return len(data_list)
        except Exception as e:
            print(f"❌ [Database] 写入失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_training_data(self, limit=100000):
        """获取最新的 N 条数据用于训练"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(f"SELECT price FROM ticks ORDER BY timestamp DESC LIMIT {limit}")
        rows = c.fetchall()
        conn.close()
        # 数据库取出是倒序的(最新在钱)，转回正序
        return [r[0] for r in rows][::-1]