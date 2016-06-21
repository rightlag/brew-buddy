import unittest
import brewbuddy


class BrewBuddyTestCase(unittest.TestCase):
    def setUp(self):
        brewbuddy.app.config['TESTING'] = True
        self.app = brewbuddy.app.test_client()

    def test_status_code(self):
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)

    def test_login(self):
        """Test OAuth login. By default, it should redirect the user to
        the GitHub login page to ask the user for authorization."""
        res = self.app.get('/login')
        self.assertEqual(res.status_code, 302)
        self.assertIn('Location', res.headers)
        self.assertIsNotNone(res.headers['Location'])

    def test_commit(self):
        pass

if __name__ == '__main__':
    unittest.main()
