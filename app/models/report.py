import sqlite3

def get_db_connection():
    conn = sqlite3.connect('instance/database.db')
    conn.row_factory = sqlite3.Row
    return conn

class Report:
    @staticmethod
    def create(driver_id, route_id, status, latitude=None, longitude=None):
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

    @staticmethod
    def get_by_id(report_id):
        conn = get_db_connection()
        report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        conn.close()
        return dict(report) if report else None

    @staticmethod
    def get_all():
        conn = get_db_connection()
        reports = conn.execute('SELECT * FROM reports ORDER BY created_at DESC').fetchall()
        conn.close()
        return [dict(row) for row in reports]
        
    @staticmethod
    def get_by_route(route_id):
        conn = get_db_connection()
        reports = conn.execute('SELECT * FROM reports WHERE route_id = ? ORDER BY created_at DESC', (route_id,)).fetchall()
        conn.close()
        return [dict(row) for row in reports]

    @staticmethod
    def update_status(report_id, status):
        conn = get_db_connection()
        conn.execute('UPDATE reports SET status = ? WHERE id = ?', (status, report_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(report_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
        conn.commit()
        conn.close()
