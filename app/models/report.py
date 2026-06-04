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

class Report:
    @staticmethod
    def create(data=None, **kwargs):
        """
        新增一筆路況/車況回報記錄。
        
        :param data: 字典型態的資料，包含 'driver_id', 'route_id', 'status', 'latitude', 'longitude'
        :param kwargs: 關鍵字引數，相容原本的參數傳遞方式 (driver_id, route_id, status, latitude, longitude)
        :return: 新增成功的報告 ID (int)，若失敗則傳回 None
        """
        if data is None:
            data = kwargs
            
        driver_id = data.get('driver_id')
        route_id = data.get('route_id')
        status = data.get('status')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO reports (driver_id, route_id, status, latitude, longitude) 
                   VALUES (?, ?, ?, ?, ?)''',
                (driver_id, route_id, status, latitude, longitude)
            )
            conn.commit()
            report_id = cursor.lastrowid
            conn.close()
            return report_id
        except Exception as e:
            print(f"Error in Report.create: {e}")
            return None

    @staticmethod
    def get_by_id(report_id):
        """
        根據 ID 取得單筆回報記錄。
        
        :param report_id: 回報記錄 ID (int)
        :return: 包含回報資料的字典 (dict)，若找不到或錯誤則傳回 None
        """
        try:
            conn = get_db_connection()
            report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
            conn.close()
            return dict(report) if report else None
        except Exception as e:
            print(f"Error in Report.get_by_id: {e}")
            return None

    @staticmethod
    def get_all():
        """
        取得所有回報記錄，包含司機姓名，依時間降序排列。
        
        :return: 回報記錄字典組成的列表 (list of dict)
        """
        try:
            conn = get_db_connection()
            reports = conn.execute(
                '''SELECT r.*, d.name AS driver_name 
                   FROM reports r 
                   JOIN drivers d ON r.driver_id = d.id 
                   ORDER BY r.created_at DESC'''
            ).fetchall()
            conn.close()
            return [dict(row) for row in reports]
        except Exception as e:
            print(f"Error in Report.get_all: {e}")
            return []
            
    @staticmethod
    def get_by_route(route_id):
        """
        根據路線 ID 取得所有回報記錄，包含司機姓名，依時間降序排列。
        
        :param route_id: 路線 ID (str)
        :return: 該路線的回報記錄字典列表 (list of dict)
        """
        try:
            conn = get_db_connection()
            reports = conn.execute(
                '''SELECT r.*, d.name AS driver_name 
                   FROM reports r 
                   JOIN drivers d ON r.driver_id = d.id 
                   WHERE r.route_id = ? 
                   ORDER BY r.created_at DESC''', 
                (route_id,)
            ).fetchall()
            conn.close()
            return [dict(row) for row in reports]
        except Exception as e:
            print(f"Error in Report.get_by_route: {e}")
            return []

    @staticmethod
    def update(report_id, data=None, **kwargs):
        """
        更新回報記錄。
        
        :param report_id: 欲更新的報告 ID (int)
        :param data: 字典型態的資料，可包含 'status'
        :param kwargs: 關鍵字引數，相容原本的參數傳遞方式 (status)
        :return: 是否更新成功 (bool)
        """
        if data is None:
            data = kwargs
            
        status = data.get('status')
        
        try:
            conn = get_db_connection()
            conn.execute('UPDATE reports SET status = ? WHERE id = ?', (status, report_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error in Report.update: {e}")
            return False

    @staticmethod
    def delete(report_id):
        """
        刪除回報記錄。
        
        :param report_id: 欲刪除的報告 ID (int)
        :return: 是否刪除成功 (bool)
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error in Report.delete: {e}")
            return False
