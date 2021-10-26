import datetime
from . import db
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_login import UserMixin


class User(db.Model, UserMixin):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), unique=True, nullable=False)
	encrypted_password = db.Column(db.String(94), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.datetime.now())
	tests = db.relationship('Test', lazy='dynamic')
	def verify_password(self, password):
		return check_password_hash(self.encrypted_password, password)

	""" PARA ACORTAR MENSAJES EN TABLAS
		ponemos litte_text en la tabla
		test.little_text

	@property
	def little_text(self):
		if len(self.description) > 20:
			return self.description[0:19] + "..."
		return self.description
    """    
	@property
	def password(self):
		pass

	@password.setter
	def password(self, value):
		self.encrypted_password = generate_password_hash(value, 'sha256')

	def __str__(self):
		return self.username

	@classmethod
	def create_element(cls, username, password, email):
		user = User(username=username, password=password, email=email)

		db.session.add(user)
		db.session.commit()
		
		return user

	@classmethod
	def get_by_username(cls, username):
		return User.query.filter_by(username=username).first()

	@classmethod
	def get_by_id(cls, id):
		return User.query.filter_by(id=id).first()


class Test(db.Model):
	__tablename__ = 'tests'

	id_test = db.Column(db.Integer, primary_key=True)
	name_test = db.Column(db.String(80), nullable=False)
	matter_test = db.Column(db.String(50), nullable=False)
	grade_test = db.Column(db.String(50), nullable=False)
	number_test = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	quests= db.relationship('Quest', cascade = "all, delete, delete-orphan")

	@classmethod
	def create_element(cls, name_test, matter_test, grade_test, number_test, user_id):
		test = Test(name_test=name_test.upper(), matter_test=matter_test.upper(), 
			grade_test=grade_test.upper(), number_test=number_test, user_id=user_id)
		db.session.add(test)
		db.session.commit()
		return test

	@classmethod
	def get_by_id(cls, id_test):
		return Test.query.filter_by(id_test=id_test).first()

	@classmethod
	def update_element(cls, id_test, name_test, matter_test, grade_test):
		test = Test.get_by_id(id_test)

		if test is None:
			return False

		test.name_test = name_test.upper()
		test.matter_test = matter_test.upper()
		test.grade_test = grade_test.upper() 

		db.session.add(test)
		db.session.commit()

		return test


	@classmethod
	def delete_element(cls, id_test):

		test = Test.get_by_id(id_test)

		if test is None:
			return False

		db.session.delete(test)
		db.session.commit()

		return True

	

class Quest(db.Model):
	__tablename__ = 'quests'

	id_quest = db.Column(db.Integer, primary_key=True)
	quest = db.Column(db.String(200), nullable=False)
	answer = db.Column(db.String(200), nullable=False)
	test_id = db.Column(db.Integer, db.ForeignKey('tests.id_test'), nullable=False)

	

	@property
	def little_quest(self):
		if len(self.quest) > 20:
			return self.quest[0:19] + "..."
		return self.quest

	@classmethod
	def create_element(cls, quest, answer, test_id):
		quest = Quest(quest=quest, answer=answer, test_id=test_id)
		db.session.add(quest)
		db.session.commit()
		return quest

	@classmethod
	def get_by_id(cls, id_quest):
		return Quest.query.filter_by(id_quest=id_quest).first()


	@classmethod
	def update_quest(cls, id_quest, quest, answer):
		question = Quest.get_by_id(id_quest)

		if quest is None:
			return False

		question.quest = quest
		question.answer = answer

		db.session.add(question)
		db.session.commit()

		return quest


