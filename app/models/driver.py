import sqlite3

# 資料庫連線輔助函式
def get_db_connection():
    conn = sqlite3.connect('instance/database.db')
    conn.row_factory = sqlite3.Row
    return conn

class Driver:
    @staticmethod
    def create(username, password_hash, name):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO drivers (username, password_hash, name) VALUES (?, ?, ?)',
            (username, password_hash, name)
        )
        conn.commit()
        driver_id = cursor.lastrowid
        conn.close()
        return driver_id

    @staticmethod
    def get_by_id(driver_id):
        conn = get_db_connection()
        driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
        conn.close()
        return dict(driver) if driver else None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        driver = conn.execute('SELECT * FROM drivers WHERE username = ?', (username,)).fetchone()
        conn.close()
        return dict(driver) if driver else None

    @staticmethod
    def update(driver_id, name=None, password_hash=None):
        conn = get_db_connection()
        if name:
            conn.execute('UPDATE drivers SET name = ? WHERE id = ?', (name, driver_id))
        if password_hash:
            conn.execute('UPDATE drivers SET password_hash = ? WHERE id = ?', (password_hash, driver_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(driver_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
        conn.commit()
        conn.close()
