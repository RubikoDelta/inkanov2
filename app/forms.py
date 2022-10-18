from wtforms import Form
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms import validators
from wtforms.fields.html5 import EmailField
from wtforms_sqlalchemy.fields import QuerySelectField


from .models import User, Test, Quest




def codi_validator(form, field):
	if field.data == 'codi' or field.data =='CODI':
		raise validators.ValidationError('el username codi no es permitido.')

class LoginForm(Form):
	username = StringField('Username', [
		validators.length(min=4, max=50, message='el usuario se encuentra fuera de rango')
		])
	password = PasswordField('Password',[
		validators.Required(message="password requerido")
		])

class RegisterForm(Form):
	username = StringField('Username', [
		validators.length(min=4, max=50, message='el usuario se encuentra fuera de rango'),
		codi_validator

		])

	email = EmailField('Email', [
		validators.length(min=6, max=100),
		validators.Required(message='email requerido.'),
		validators.Email(message='Ingrese un mensaje valido')
		])

	password = PasswordField('Password',[
		validators.Required(message="password requerido"),
		validators.EqualTo('confirm_password', message='la contraseña no coincide')
		])
	confirm_password = PasswordField('Confirm password')
	accept = BooleanField('', [
		validators.DataRequired()

		])

	def validate_username(self, username):
		if User.get_by_username(username.data):
			raise validators.ValidationError('El username se encuentra en uso.')

class TestForm(Form):
	name_test = StringField('(Para identificarlo más facilmente)', [
		validators.length(min=4, max=80, message="Nombre fuera de rango"),
		validators.DataRequired(message='El nombre es requerido')
		])
	matter_test = StringField('Materia del cuestionario:', [
		validators.DataRequired(message='Materia requerida.')
		])
	grade_test = StringField('Grado correspondiente:', [
		validators.DataRequired(message='Grado requerido.')
		])
	number_test = SelectField('(Debe ser par, para un mejor funcionamiento del juego)',
		choices=[(4,'4'), (6,'6'), (8,'8'),(10,'10'), (12,'12'), (14, '14'),
		 (16, '16'), (18,'18'), (20,'20'), (22,'22'),
		 (24,'24'), (26,'26'), (28,'28'), (30,'30')])


class QuestForm(Form):
	quest = StringField('Pregunta', [
		validators.DataRequired(message='Campo requerido.'),
		validators.length(min=1, max=200, message="Nombre fuera de rango")
		])
	answer = StringField('Respuesta', [
		validators.DataRequired(message='Campo requerido.'),
		validators.length(min=1, max=200, message="Nombre fuera de rango")
		])
	answer1 = StringField('Primera respuesta equivocada', [
		validators.DataRequired(message='Campo requerido.'),
		validators.length(min=1, max=200, message="Nombre fuera de rango")
		])
	answer2 = StringField('Segunda respuesta equivocada', [
		validators.DataRequired(message='Campo requerido.'),
		validators.length(min=1, max=200, message="Nombre fuera de rango")
		])
	answer3 = StringField('Tercera respuesta equivocada', [
		validators.DataRequired(message='Campo requerido.'),
		validators.length(min=1, max=200, message="Nombre fuera de rango")
		])


def choice_grade_query():
	return Test.query.group_by(Test.grade_test)

class ChoiceGradeForm(Form):
	grades = QuerySelectField('Selecciona el grado', query_factory=choice_grade_query, get_label='grade_test')

class ChoiceTestForm(Form):	
	tests = SelectField('Seleccione cuestionario', choices=[])
	dificultad= SelectField('Seleccione el nivel de dificultad', choices=[('Facil', 'Facil'), ('Medio', 'Medio'), ('Dificil', 'Dificil')])

class ChoiceMatterForm(Form):
	matters = SelectField('Seleccione materia o curso', choices=[])

class StartForm(Form):
	"""
	player1 = StringField('Ingresar el nombre del primer jugador, no mayor a 10 letras',  [
		validators.length(min=3, max=10, message='el nombre se encuentra fuera de rango'),
		validators.DataRequired(message='El nombre es requerido')
		])
		
	player2 = StringField('Ingresar el nombre del segundo jugador, no mayor a 10 letras', [
		validators.length(min=3, max=10, message='el nombre se encuentra fuera de rango'),
		validators.DataRequired(message='El nombre es requerido')
		])
	"""
	time = SelectField('Selecciona el tiempo máximo (en segundos) para responder a cada pregunta',
		choices=[(5,'5'), (10,'10'), (15,'15'), (20, '20'), (25,'25'), (30,'30')])
	