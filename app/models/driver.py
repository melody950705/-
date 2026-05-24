import sqlite3

def get_db_connection():
    """
    建立與 SQLite 資料庫的連線。
    
    Returns:
        sqlite3.Connection: 資料庫連線物件，且設定 row_factory 為 sqlite3.Row
    """
    try:
        conn = sqlite3.connect('instance/database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise e

class Driver:
    @staticmethod
    def create(data):
        """
        新增一筆司機記錄。
        
        Args:
            data (dict): 包含 'username', 'password_hash', 'name' 的字典
            
        Returns:
            int: 新建立的司機 ID，若失敗則為 None
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO drivers (username, password_hash, name) VALUES (?, ?, ?)',
                (data['username'], data['password_hash'], data['name'])
            )
            conn.commit()
            driver_id = cursor.lastrowid
            conn.close()
            return driver_id
        except sqlite3.Error as e:
            print(f"Error creating driver: {e}")
            return None

    @staticmethod
    def get_by_id(driver_id):
        """
        取得指定 ID 的單筆司機記錄。
        
        Args:
            driver_id (int): 司機 ID
            
        Returns:
            dict: 司機資料字典，若找不到或失敗則傳回 None
        """
        try:
            conn = get_db_connection()
            row = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting driver by id {driver_id}: {e}")
            return None

    @staticmethod
    def get_by_username(username):
        """
        根據使用者名稱取得單筆司機記錄。
        
        Args:
            username (str): 司機登入帳號
            
        Returns:
            dict: 司機資料字典，若找不到或失敗則傳回 None
        """
        try:
            conn = get_db_connection()
            row = conn.execute('SELECT * FROM drivers WHERE username = ?', (username,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting driver by username {username}: {e}")
            return None

    @staticmethod
    def get_all():
        """
        取得所有司機記錄。
        
        Returns:
            list: 包含所有司機資料字典的清單，若失敗則傳回空清單
        """
        try:
            conn = get_db_connection()
            rows = conn.execute('SELECT * FROM drivers').fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting all drivers: {e}")
            return []

    @staticmethod
    def update(driver_id, data):
        """
        更新指定 ID 的司機記錄。
        
        Args:
            driver_id (int): 司機 ID
            data (dict): 包含要更新之欄位的字典 (e.g., 'name', 'password_hash')
            
        Returns:
            bool: 更新成功傳回 True，失敗傳回 False
        """
        try:
            conn = get_db_connection()
            fields = []
            values = []
            for key, val in data.items():
                if key in ('username', 'name', 'password_hash'):
                    fields.append(f"{key} = ?")
                    values.append(val)
            
            if not fields:
                conn.close()
                return False
                
            values.append(driver_id)
            query = f"UPDATE drivers SET {', '.join(fields)} WHERE id = ?"
            conn.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error updating driver {driver_id}: {e}")
            return False

    @staticmethod
    def delete(driver_id):
        """
        刪除指定 ID 的司機記錄。
        
        Args:
            driver_id (int): 司機 ID
            
        Returns:
            bool: 刪除成功傳回 True，失敗傳回 False
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting driver {driver_id}: {e}")
            return False
