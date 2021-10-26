import unittest

from flask import current_app

from app import create_app
from app import db, User, Test, Quest

class DemoTestCase(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_demo(self):
		self.assertTrue( 1 == 1 )

