class Config:
	SECRET_KEY = 'practicafinal2021'
	UPLOAD_FOLDER = 'static/uploads'
	#SERVER_NAME = '192.168.2.104:5000'

class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'mysql://root:admin@localhost/project_inkano?charset=utf8mb4'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_ENGINE_OPTIONS={
		'isolation_level':'READ UNCOMMITTED'
	}
config = {
	'development': DevelopmentConfig, 
	'default': DevelopmentConfig
}