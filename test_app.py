import unittest
import os
import sqlite3
from app import create_app, init_db
from app.models.driver import Driver
from app.models.report import Report
from werkzeug.security import generate_password_hash

class TaichungBusTestCase(unittest.TestCase):
    def setUp(self):
        """
        Set up a test environment: use an in-memory or temporary database,
        initialize the schema, and configure the Flask app in testing mode.
        """
        # Define a temporary database path for testing
        self.db_path = 'instance/test_database.db'
        
        # Override the database config dynamically
        class TestConfig:
            TESTING = True
            SECRET_KEY = 'test-secret-key'
            DATABASE = self.db_path
            
        # Ensure we start with a clean state
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        # Initialize schema in test database
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        # Create Flask App
        self.app = create_app(config_class=TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Monkey patch get_db_connection in model files to point to test database
        import app.models.driver
        import app.models.report
        
        def test_get_db_connection():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
            
        app.models.driver.get_db_connection = test_get_db_connection
        app.models.report.get_db_connection = test_get_db_connection

    def tearDown(self):
        """
        Clean up the test environment.
        """
        self.app_context.pop()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_model_driver_crud(self):
        """
        Test driver creation, retrieval, updating, and deletion.
        """
        # Create
        data = {
            "username": "test_driver",
            "password_hash": generate_password_hash("abc12345"),
            "name": "陳阿生"
        }
        driver_id = Driver.create(data)
        self.assertIsNotNone(driver_id)
        
        # Retrieve by username
        driver = Driver.get_by_username("test_driver")
        self.assertIsNotNone(driver)
        self.assertEqual(driver["name"], "陳阿生")
        
        # Retrieve by ID
        driver_by_id = Driver.get_by_id(driver_id)
        self.assertIsNotNone(driver_by_id)
        self.assertEqual(driver_by_id["username"], "test_driver")
        
        # Update
        update_data = {"name": "陳先生"}
        success = Driver.update(driver_id, update_data)
        self.assertTrue(success)
        driver_updated = Driver.get_by_id(driver_id)
        self.assertEqual(driver_updated["name"], "陳先生")
        
        # Delete
        del_success = Driver.delete(driver_id)
        self.assertTrue(del_success)
        self.assertIsNone(Driver.get_by_id(driver_id))

    def test_model_report_crud(self):
        """
        Test report creation, route querying, and deletion.
        """
        # Create a driver first for foreign key constraint
        drv_id = Driver.create({
            "username": "driver_rep",
            "password_hash": "dummy_hash",
            "name": "李司機"
        })
        
        # Create Report
        rep_data = {
            "driver_id": drv_id,
            "route_id": "310",
            "status": "滿載",
            "latitude": 24.156,
            "longitude": 120.645
        }
        report_id = Report.create(rep_data)
        self.assertIsNotNone(report_id)
        
        # Retrieve by ID
        report = Report.get_by_id(report_id)
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "滿載")
        
        # Retrieve by Route
        route_reports = Report.get_by_route("310")
        self.assertEqual(len(route_reports), 1)
        self.assertEqual(route_reports[0]["driver_name"], "李司機")
        
        # Delete
        del_success = Report.delete(report_id)
        self.assertTrue(del_success)
        self.assertIsNone(Report.get_by_id(report_id))

    def test_report_normal_override(self):
        """
        Test that reporting "正常行駛" clears/overwrites previous reports for that route.
        """
        drv_id = Driver.create({
            "username": "driver_ovr",
            "password_hash": "dummy_hash",
            "name": "陳司機"
        })
        
        # Create abnormal reports on route "300"
        Report.create(driver_id=drv_id, route_id="300", status="滿載")
        Report.create(driver_id=drv_id, route_id="300", status="車多延誤")
        
        # Assert they are both there
        reports = Report.get_by_route("300")
        self.assertEqual(len(reports), 2)
        
        # Now report "正常行駛"
        Report.create(driver_id=drv_id, route_id="300", status="正常行駛")
        
        # Assert previous reports are deleted, and only "正常行駛" remains
        reports_after = Report.get_by_route("300")
        self.assertEqual(len(reports_after), 1)
        self.assertEqual(reports_after[0]["status"], "正常行駛")
        self.assertEqual(reports_after[0]["driver_name"], "陳司機")

    def test_http_routes(self):
        """
        Test various routes to ensure they return the expected status codes.
        """
        # Homepage
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        
        # Route plan page
        res = self.client.get('/route-plan')
        self.assertEqual(res.status_code, 200)
        
        # Route plan page with parameters
        res = self.client.get('/route-plan?start=台中車站&end=逢甲大學')
        self.assertEqual(res.status_code, 200)
        html_data = res.get_data(as_text=True)
        self.assertIn("乘車：", html_data)
        self.assertIn("步行：", html_data)
        
        # Specific route status page
        res = self.client.get('/bus/300')
        self.assertEqual(res.status_code, 200)
        
        # API bus status
        res = self.client.get('/api/bus/300')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["route_id"], "300")
        self.assertIn("stops", json_data)
        
        # Driver Login page
        res = self.client.get('/driver/login')
        self.assertEqual(res.status_code, 200)
        
        # Driver Report page (without login - should redirect to login)
        res = self.client.get('/driver/report')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/driver/login', res.headers.get('Location'))

    def test_api_nearby_stops(self):
        """
        Test /api/nearby-stops route to ensure it returns 200 and the stops list.
        """
        # Test without parameters (falls back to default)
        res = self.client.get('/api/nearby-stops')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("stops", json_data)
        self.assertTrue(len(json_data["stops"]) > 0)
        
        # Test with parameters
        res = self.client.get('/api/nearby-stops?lat=24.1373&lng=120.6868')  # Taichung Station
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["stops"][0]["name"], "台中車站 (Taichung Station)")

if __name__ == '__main__':
    unittest.main()
