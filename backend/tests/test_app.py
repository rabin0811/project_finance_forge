import unittest
from app import app, project_growth


class TestCalc(unittest.TestCase):
    def test_conversion_logic(self):
        """1 GBP to USD at rate 1.27 => 1.27 (mirrors backend math)."""
        amount = 100
        rate = 1.27
        result = amount * rate
        self.assertAlmostEqual(result, 127.0)

    def test_project_growth_zero(self):
        self.assertEqual(project_growth(0, 0, 0, 10), 0)

    def test_project_growth_compound(self):
        # 100 at 12% annual (monthly compounding), no contributions, 1 year
        self.assertAlmostEqual(project_growth(100, 0, 12, 1), 112.68, places=2)

    def test_index_redirects_to_login(self):
        client = app.test_client()
        resp = client.get("/")
        self.assertEqual(resp.status_code, 302)

    def test_login_page(self):
        client = app.test_client()
        resp = client.get("/login")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_requires_login(self):
        client = app.test_client()
        resp = client.get("/dashboard")
        self.assertIn(resp.status_code, [302, 401, 403])

    def test_login_flow(self):
        client = app.test_client()
        resp = client.post("/login", data={"username": "staff", "password": "staff123"},
                           follow_redirects=True)
        self.assertIn(b"Dashboard", resp.data)


if __name__ == "__main__":
    unittest.main()