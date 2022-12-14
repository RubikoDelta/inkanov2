import datetime
from enum import unique
from . import db
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT, TEXT, BINARY


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

	"""@classmethod
	def update_element(cls, username, state):
		user = User.get_by_username(username)

		if user is None:
			return False

		user.player = state
		

		db.session.add(user)
		db.session.commit()

		return user"""


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

		quest = Quest.query.filter_by(test_id=id_test).all()
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
	def get_ans(cls, id_test):
		quest = Quest.query.filter_by(test_id=id_test).first()
		count = Ans.query.filter_by(quest_id = quest.id_quest).count()
		if count == 0:
			return False
		else:
			return True

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

class Image(db.Model):
	__tablename__ = 'image'
	id= db.Column(db.Integer, primary_key=True)
	quest_id = db.Column(db.Integer, db.ForeignKey('quests.id_quest'), nullable=False)
	#img = db.Column(LONGTEXT, nullable=False)
	name = db.Column(db.TEXT, nullable=False)
	@classmethod
	def create_element(cls,name,quest_id):
		imagen = Image(name=name,quest_id=quest_id)
		db.session.add(imagen)
		db.session.commit()
		return True

class Ans(db.Model):
	__tablename__ = 'other_ans'
	id= db.Column(db.Integer, primary_key=True)
	quest_id = db.Column(db.Integer, db.ForeignKey('quests.id_quest'), nullable=False)
	answer1 = db.Column(db.String(200), nullable=False)
	answer2 = db.Column(db.String(200), nullable=False)
	answer3 = db.Column(db.String(200), nullable=False)
	@classmethod
	def create_element(cls,quest_id,answer1,answer2,answer3):
		other_ans = Ans(quest_id=quest_id,answer1=answer1,answer2=answer2,answer3=answer3)
		db.session.add(other_ans)
		db.session.commit()
		return True


class Player(db.Model, UserMixin):
	__tablename__ = 'players'

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), unique=True, nullable=False)
	score = db.Column(db.Integer)

	@classmethod
	def delete_user(cls):
		player = Player.query.all()
		for i in player:
			db.session.delete(i)
			db.session.commit()
		return True

	@classmethod
	def get_by_username(cls, username):
		return Player.query.filter_by(username=username).first()
	
	@classmethod
	def update_score(cls, username,score):
		player = Player.get_by_username(username)

		if player is None:
			return False

		player.username = username
		player.score=score

		db.session.add(player)
		db.session.commit()

		return player


	@classmethod
	def create_element(cls,username):
		player= Player(username=username)
		db.session.add(player)
		db.session.commit()
		return True
	
	@classmethod
	def delete_players(cls, username):
		user = Player.get_by_username(username)
		db.session.delete(user)
		db.session.commit()
		return True