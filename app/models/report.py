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

class Report:
    @staticmethod
    def create(data):
        """
        新增一筆回報記錄。
        
        Args:
            data (dict): 包含 'driver_id', 'route_id', 'status', 'latitude' (選填), 'longitude' (選填) 的字典
            
        Returns:
            int: 新建立的回報 ID，若失敗則為 None
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO reports (driver_id, route_id, status, latitude, longitude) 
                   VALUES (?, ?, ?, ?, ?)''',
                (
                    data['driver_id'],
                    data['route_id'],
                    data['status'],
                    data.get('latitude'),
                    data.get('longitude')
                )
            )
            conn.commit()
            report_id = cursor.lastrowid
            conn.close()
            return report_id
        except sqlite3.Error as e:
            print(f"Error creating report: {e}")
            return None

    @staticmethod
    def get_by_id(report_id):
        """
        取得指定 ID 的單筆回報記錄。
        
        Args:
            report_id (int): 回報 ID
            
        Returns:
            dict: 回報資料字典，若找不到或失敗則傳回 None
        """
        try:
            conn = get_db_connection()
            row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting report by id {report_id}: {e}")
            return None

    @staticmethod
    def get_all():
        """
        取得所有回報記錄，依建立時間降冪排序，並關聯司機姓名。
        
        Returns:
            list: 包含所有回報資料字典的清單，若失敗則傳回空清單
        """
        try:
            conn = get_db_connection()
            query = '''
                SELECT r.*, d.name as driver_name 
                FROM reports r 
                LEFT JOIN drivers d ON r.driver_id = d.id 
                ORDER BY r.created_at DESC
            '''
            rows = conn.execute(query).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting all reports: {e}")
            return []
        
    @staticmethod
    def get_by_route(route_id):
        """
        取得特定公車路線的所有回報記錄，依建立時間降冪排序，並關聯司機姓名。
        
        Args:
            route_id (str): 公車路線代號
            
        Returns:
            list: 該路線的回報記錄清單，若失敗則傳回空清單
        """
        try:
            conn = get_db_connection()
            query = '''
                SELECT r.*, d.name as driver_name 
                FROM reports r 
                LEFT JOIN drivers d ON r.driver_id = d.id 
                WHERE r.route_id = ? 
                ORDER BY r.created_at DESC
            '''
            reports = conn.execute(query, (route_id,)).fetchall()
            conn.close()
            return [dict(row) for row in reports]
        except sqlite3.Error as e:
            print(f"Error getting reports by route {route_id}: {e}")
            return []

    @staticmethod
    def update(report_id, data):
        """
        更新指定 ID 的回報記錄。
        
        Args:
            report_id (int): 回報 ID
            data (dict): 包含要更新之欄位的字典 (e.g., 'status', 'route_id', 'latitude', 'longitude')
            
        Returns:
            bool: 更新成功傳回 True，失敗傳回 False
        """
        try:
            conn = get_db_connection()
            fields = []
            values = []
            allowed_fields = ('driver_id', 'route_id', 'status', 'latitude', 'longitude')
            for key, val in data.items():
                if key in allowed_fields:
                    fields.append(f"{key} = ?")
                    values.append(val)
            
            if not fields:
                conn.close()
                return False
                
            values.append(report_id)
            query = f"UPDATE reports SET {', '.join(fields)} WHERE id = ?"
            conn.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error updating report {report_id}: {e}")
            return False

    @staticmethod
    def delete(report_id):
        """
        刪除指定 ID 的回報記錄。
        
        Args:
            report_id (int): 回報 ID
            
        Returns:
            bool: 刪除成功傳回 True，失敗傳回 False
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting report {report_id}: {e}")
            return False
