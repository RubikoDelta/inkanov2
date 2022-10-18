from app import create_app, socketio
from app import db, User, Test, Quest

from flask_script import Manager, Shell
from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate, MigrateCommand

from config import config

config_class = config['development']
app = create_app(config_class)
#app.config['SERVER_NAME'] = 'http://192.168.2.104:5000/'
#migrate = Migrate(app, db)


def make_shell_context():
	return dict(app=app, db=db, User=User, Test=Test, Quest=Quest)

if __name__ == '__main__':
	manager = Manager(app)
	socketio.run(app)
	manager.add_command('shell', Shell(make_context=make_shell_context) )
	#manager.add_command('db', MigrateCommand)


	@manager.command
	def test():
		import unittest
		tests = unittest.TestLoader().discover('tests')
		unittest.TextTestRunner().run(tests)

	manager.run()
