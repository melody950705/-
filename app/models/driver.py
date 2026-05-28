import os
import sqlite3

def get_db_connection():
    """
    建立並回傳 SQLite 資料庫連線。
    
    設定 row_factory 為 sqlite3.Row，使查詢結果能以欄位名稱進行存取。
    使用絕對路徑以避免在不同工作目錄下執行時找不到 database.db。
    
    :return: sqlite3.Connection 連線物件
    """
    # 確保以專案根目錄的絕對路徑存取 database.db
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, 'instance', 'database.db')
    
    # 確保 instance 目錄存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class Driver:
    @staticmethod
    def create(data=None, **kwargs):
        """
        新增一筆司機記錄。
        
        :param data: 字典型態的資料，包含 'username', 'password_hash', 'name'
        :param kwargs: 關鍵字引數，相容原本的參數傳遞方式 (username, password_hash, name)
        :return: 新增成功的司機 ID (int)，若失敗則傳回 None
        """
        if data is None:
            data = kwargs
            
        username = data.get('username')
        password_hash = data.get('password_hash')
        name = data.get('name')
        
        try:
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
        except Exception as e:
            print(f"Error in Driver.create: {e}")
            return None

    @staticmethod
    def get_by_id(driver_id):
        """
        根據 ID 取得單筆司機記錄。
        
        :param driver_id: 司機 ID (int)
        :return: 包含司機資料的字典 (dict)，若找不到或錯誤則傳回 None
        """
        try:
            conn = get_db_connection()
            driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
            conn.close()
            return dict(driver) if driver else None
        except Exception as e:
            print(f"Error in Driver.get_by_id: {e}")
            return None

    @staticmethod
    def get_by_username(username):
        """
        根據登入帳號取得單筆司機記錄。
        
        :param username: 司機帳號 (str)
        :return: 包含司機資料的字典 (dict)，若找不到或錯誤則傳回 None
        """
        try:
            conn = get_db_connection()
            driver = conn.execute('SELECT * FROM drivers WHERE username = ?', (username,)).fetchone()
            conn.close()
            return dict(driver) if driver else None
        except Exception as e:
            print(f"Error in Driver.get_by_username: {e}")
            return None

    @staticmethod
    def get_all():
        """
        取得所有司機的記錄。
        
        :return: 司機資料字典組成的列表 (list of dict)
        """
        try:
            conn = get_db_connection()
            drivers = conn.execute('SELECT * FROM drivers ORDER BY created_at DESC').fetchall()
            conn.close()
            return [dict(row) for row in drivers]
        except Exception as e:
            print(f"Error in Driver.get_all: {e}")
            return []

    @staticmethod
    def update(driver_id, data=None, **kwargs):
        """
        更新司機記錄。
        
        :param driver_id: 欲更新的司機 ID (int)
        :param data: 字典型態的資料，可包含 'name', 'password_hash'
        :param kwargs: 關鍵字引數，相容原本的參數傳遞方式 (name, password_hash)
        :return: 是否更新成功 (bool)
        """
        if data is None:
            data = kwargs
            
        name = data.get('name')
        password_hash = data.get('password_hash')
        
        try:
            conn = get_db_connection()
            if name:
                conn.execute('UPDATE drivers SET name = ? WHERE id = ?', (name, driver_id))
            if password_hash:
                conn.execute('UPDATE drivers SET password_hash = ? WHERE id = ?', (password_hash, driver_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error in Driver.update: {e}")
            return False

    @staticmethod
    def delete(driver_id):
        """
        刪除司機記錄。
        
        :param driver_id: 欲刪除的司機 ID (int)
        :return: 是否刪除成功 (bool)
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error in Driver.delete: {e}")
            return False
