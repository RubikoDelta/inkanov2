class Config:
	SECRET_KEY = 'practicafinal2021'

class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'mysql://root:5647040621i@localhost/project_inkano'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
config = {
	'development': DevelopmentConfig, 
	'default': DevelopmentConfig
}