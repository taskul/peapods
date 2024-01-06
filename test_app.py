from unittest import TestCase
from app import app
from flask import session

app.config['TESTING'] = True

class HomePageTestCase(TestCase):
    '''Testing the home page route'''
    def test_home(self):
        with app.test_client() as client:
            resp = client.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('Profile', html)

