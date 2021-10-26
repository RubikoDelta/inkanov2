from flask import Blueprint, session
from flask import render_template, request, flash, redirect, url_for, abort
from flask import current_app
from flask import send_from_directory
from . import db
from flask import send_file
import shutil
import re, random, time
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import cast, Numeric, func, Integer
from .forms import LoginForm, RegisterForm, TestForm, ChoiceMatterForm, QuestForm, ChoiceGradeForm, ChoiceTestForm, StartForm 
from .models import User, Test, Quest
from . import login_manager
import os.path
import os








page = Blueprint('page', __name__)


#________________APARTADO DE: REGISTRO Y LOGIN DE USUARIOS____________________

@login_manager.user_loader
def load_user(id):
	return User.get_by_id(id)

#Página que controla rutas no definadas
@page.app_errorhandler(404)
def page_not_found(error):
	return render_template('errors/404.html'), 404

#Index donde estaran los botones para las principales páginas
@page.route('/')
def index():
	return render_template('index.html', title='Index')

#Ruta para cerrar sesión
@page.route('/logout')
def logout():
	logout_user()
	flash('Sesión terminada.')
	return redirect(url_for('.login'))
'''
Ruta hacia la página de inicio de sesión
Esta clase se encarga del proceso de inicio de sesion de los usarios YA registraados.
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/login', methods=['POST', 'GET'])
def login():

	if current_user.is_authenticated:
		return redirect(url_for('.index'))

	#Declaramos el formulario (desde el archivo forms.py)
	form = LoginForm(request.form)

	if request.method == 'POST' and form.validate():
		#creamos la variable y le asignamos desde una consulta de la tabla User, en el filtro le decimos que sea igual al username que mando el usuario en el form
		user = User.get_by_username(form.username.data)

		#Aqui verificamos si el usuario en verdad existe y comprobamos si la contraseña es correcta
		if user and user.verify_password(form.password.data):
			login_user(user)
			return redirect(url_for('.index'))
			flash('Usuario autenticado Exitosamente')
		else:
			flash('Datos incorrectos.', 'error')

	return render_template('auth/login.html', title='Login', form=form, active='login')

'''
Ruta hacia la pagina de Registro
Esta página se encargara de ingresar los datos de nuevos usarios a la base de datos que luego la ruta de login usara.
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('.index'))

	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		#llamamos desde el archivo models.py el metodo create_element con los parametros que el usario lleno en el form
		user = User.create_element(form.username.data, form.password.data, form.email.data)
		flash('Usuario registrado exitosamente!')
		return redirect(url_for('.login'))

	return render_template('auth/register.html', title='Registro', form=form, active='register')

'''
Ruta y clase que muestra la lista de cuestionarios creados por el usuario actual autenticado
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests')
@page.route('/tests/<int:page>')
@login_required
def tests(page=1, per_page=10): #Paginacion: empezamos en pagina y 10 cuestionarios por página
	pagination = current_user.tests.paginate(page, per_page=per_page)
	tests = pagination.items

	return render_template('test/list.html', title='Juego',
		tests=tests, pagination = pagination, page=page,
		active='tests')


#________________APARTADO DE: GESTIÓN DE CUESTIONARIOS____________________

'''
Ruta de creacion de un nuevo cuestionario
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests/new', methods=['GET', 'POST'])
@login_required
def new_test():
	form = TestForm(request.form)

	if request.method == 'POST'and form.validate():
		number_quests = int(form.number_test.data) #guardamos el numero de preguntas
		test = Test.create_element(form.name_test.data, form.matter_test.data, form.grade_test.data, number_quests, current_user.id)
		current_test = db.session.query(Test).order_by(Test.id_test.desc()).first() #Guardamos el id del cuestionario que se acaba de crear
		if test: #Si el cuestionario se creo nos redirigimos a la ruta de creacion de preguntas
			flash('Ingrese las preguntas al nuevo cuestionario:')
			return redirect(url_for('.new_quest', current_test=current_test, number_quests=number_quests)) #Necesitamos mandar el id del cuestionario nuevo y el numero de preguntas a new_quests (/quests/new)

	return render_template('/test/new.html', title='nuevo test',
		form=form, active='new_test')

'''
Ruta que muestra datos de un cuestionario específico
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests/show/<int:test_id>')
def get_test(test_id): #test_id es obtenido desde test/list.html
	test=Test.query.get_or_404(test_id)

	return render_template('test/show.html', title="Cuestionario", test=test)

'''
página para editar los datos principales de un cuestionario
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests/edit/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit_test(test_id): #test_id es obtenido desde test/list.html

	test = Test.query.get_or_404(test_id) #Objeto para consultar datos del cuestionar a editar
	questions = test.id_test  #obtenemos el id del cuestionario, siendo este la fk de las preguntas
	int(questions) #convertimos a entero este dato.

	if test.user_id != current_user.id:
		abort(404)

	form = TestForm(request.form, obj=test)

	if request.method == 'POST' and form.validate():
		#llamamos el metodo update_element desde el archivo models.py
		test = Test.update_element(test.id_test, form.name_test.data, form.matter_test.data, form.grade_test.data)
		if test:
			flash('Cuestionario Actualizado.')
			return redirect(url_for('.tests'))

	return render_template('test/edit.html', title='Editar', form=form, questions=questions)

'''
página para eliminar un cuestionario con sus preguntas
Para eliminar consigo las preguntas se utilizo el parametro cascade = "all, delete, delete-orphan" en la clase Test en models.py
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests/delete/<int:test_id>')
@login_required
def delete_test(test_id): #test_id es obtenido desde test/list.html

	test = Test.query.get_or_404(test_id) #Declaramos un objeto con la id del cuestionario para eliminar

	if test.user_id != current_user.id:
		abort(404)

	if Test.delete_element(test.id_test):
		flash('cuestionario eliminado con exito.')
		return redirect(url_for('.tests'))


@page.route('/test/download/<int:test_id>')
@login_required
def download_test(test_id):

	test = Test.query.get_or_404(test_id) #Declaramos un objeto con la id del cuestionario para eliminar
	name = test.name_test
	grade = test.grade_test
	matter = test.matter_test
	number = test.number_test
	number_str = str(number)

	quests = Quest.query.filter_by(test_id = test_id).all()


	#Primero lo transformamos a una cadena de texto todas las ids de las preguntas
	quests = str(quests)
	#Luego obtenemos solo los numeros con la funcion re:
	for i in quests:
		quests_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', quests)]

	position = 0
	num = 1


	if test.user_id != current_user.id:
		abort(404)

	file_name = name.replace(" ", "_") + '.txt'

	file = open (file_name ,'w')
	file.write('Nombre del Cuestionario: ' +  name +'\n' )
	file.write('Grado del Cuestionario: ' + grade +'\n')
	file.write('Materia del Cuestionario: ' + matter +'\n')
	file.write('Total de preguntas: ' + number_str +'\n')
	file.write('\n')
	file.write('Preguntas:\n')
	file.write('\n')

	while position <= number - 1:
		num_str = str(num)
		current_question = Quest.query.filter_by(id_quest = quests_int[position]).first() #obtenemos la pregunta que corresponde
		question = current_question.quest #obtenemos el campo pregunta
		answer = current_question.answer #obtenemos el campo respuesta
		file.write(num_str+') '+ question +'\n')
		file.write('Respuesta:' + answer+'\n')
		file.write('\n')
		position = position +1
		num=num+1

	file.close()
	
	

	if os.path.isdir('Cuestionarios'):
		print('La carpeta existe.')
	else:
		os.mkdir('cuestionarios')

	
	cwd = os.getcwd()  #Carpeta raiz
	src = cwd
	dst = cwd + '/Cuestionarios/'

	shutil.move(os.path.join(src, file_name), os.path.join(dst, file_name))

	final_file = dst + file_name


	return send_file(final_file, as_attachment=True)


'''
página para la creacion de las preguntas del cuestionario que se acaba de crear
Última modificación Julio de 2021 por Diego Aguirre
'''
@page.route('/quests/new', methods=['GET', 'POST'])
@login_required
def new_quest():

	#Recibimos estos datos desde: new_test (/tests/new)
	current_test = request.args.get("current_test") #ultimo cuestionario creado
	number_quests = request.args.get("number_quests") #número de preguntas del cuestioanrio

	number_quests = int(number_quests) #Cast de string a Int 
	#En este momento current_test es un objeto query, similar a: <id_test: 1>
	format_str = str(current_test) #transformamos a una cadena de texto
	#Finalmente obtenemos el numero de la id con la funcion 're' donde esta nos devolvera solo los nuemeros.
	id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', format_str)] #De '<id_test: 1>' pasamos a: '1' 

	form = QuestForm(request.form)

	if request.method  == 'POST':
		if form.validate():

			quest = Quest.create_element(form.quest.data, form.answer.data, id_int[0])
			flash('Pregunta creada exitosamente')
			if quest:
				if number_quests != 1: #sirve para controlar la creacion de preguntas 
					number_quests = number_quests - 1 #Con cada pregunta creada se baja el numero de preguntas pendienetes

					
					
					#En el return usamos recursividad hacia esta misma clase:
					#Se manda nuevamente el cuestionario actual (current_test) y preguntas pedientes -1 (number_quests) 
					return redirect(url_for('.new_quest', current_test=current_test, number_quests=number_quests))

				else: 
					return redirect(url_for('.tests'))


	return render_template('quest/new.html', title='Crear Preguntas', form=form, id_int=id_int)

'''
página para listar las preguntas del cuestionario escogido en '/tests'
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/quests/<int:test_id>', methods=['GET', 'POST'])
@login_required
def quests(test_id): #test_id es obtenido desde test/list.html

	quest = Test.query.get_or_404(test_id) #Objeto query de la tabla del cuestionario

	ids_quests = str(quest)	#Primero lo transformamos a una cadena de texto
	
	id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', ids_quests)] #Luego obtenemos solo los numeros con la funcion re

	quests = Quest.query.filter_by(test_id=id_int).all() #Objeto query con la lista de las ids de todas la preguntas del cuestionario

	return render_template('quest/list.html', title='Preguntas', quests= quests)

'''
página para editar una pregunta en especifico escogida en 'quest/list.html'
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/quests/edit/<int:quest_id>', methods=['GET', 'POST'])
@login_required
def edit_quest(quest_id): #quest_id obtenido desde quest/list.html

	quest = Quest.query.get_or_404(quest_id) #Objeto query de la tabla Quest
	form = QuestForm(request.form, obj=quest)
	test_id = quest.test_id #Obtenemos el id del test para regresar a la lista de preguntas de ese cuestionario

	if request.method == 'POST' and form.validate():

		quest = Quest.update_quest(quest.id_quest, form.quest.data, form.answer.data)

		if quest:
			flash('Pregunta actualizada exitosamente')
			return redirect(url_for('.quests', test_id=test_id))

	return render_template('quest/edit.html', title='Editar pregunta', form=form)


#________________APARTADO DE: JUGABILIDAD____________________

@page.route('/game/mode', methods=['GET', 'POST'])
@login_required
def select_mode():

	if request.method == 'POST':
		if request.form['button'] == 'mode1':
				session['mode'] = 1

		elif request.form['button'] == 'mode2':
				session['mode'] = 2

		flash("Modo de juego Seleccionado")
		return redirect(url_for('.select_grade'))


	return render_template('/game/mode.html', title="Modo de Juego")



'''
página para seleccionar el grado del cuestionario a jugar
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/grade', methods=['GET', 'POST'])
@login_required
def select_grade():

	form = ChoiceGradeForm(request.form) #El campo del formulario se llena desde con todos los grados registrados desde forms.py (lineas 79 a 83)

	if request.method == 'POST':
		if form.validate():

			test_id = form.grades.data #El grado seleccionado por el usuario devuelve el id del primer cuestionario con dicho grado.
			
			#Primero lo transformamos la id a una cadena de texto 
			test_id_str = str(test_id)
			#Luego obtenemos solo los numeros con la funcion re:
			id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', test_id_str)]

			test = Test.query.get_or_404(id_int) #Objeto de consulta al registro obtenido
			grade = test.grade_test #Finalmente obtenemos el grado
			
			
			flash("Grado seleccionado.")			
			return redirect(url_for('.select_matter', grade=grade))

	return render_template('/game/grade.html', title="Seleccionar Grado", form=form)

'''
página para seleccionar la materia del cuestionario a jugar
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/<grade>', methods=['GET', 'POST'])
@login_required
def select_matter(grade):

	form = ChoiceMatterForm(request.form)
	
	#Llenamos el SelectField del form con un for que recorrera un query con todas las materias que tengan en comun al menos un cuestionario con el grado seleccionado previamente
	form.matters.choices = [(t.id_test, t.matter_test) for t in Test.query.group_by(Test.matter_test).filter_by(grade_test = grade).all()]

	if request.method == 'POST':
		if form.validate():
			test_id = form.matters.data

			#Primero lo transformamos a una cadena de texto
			test_id_str = str(test_id)
			#Luego obtenemos solo los numeros con la funcion re:
			id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', test_id_str)]

			test = Test.query.get_or_404(id_int)
			matter = test.matter_test #Obtenemos la materia
			select_grade = grade #guardamos nuevamente el grado seleccionado
			flash("Materia seleccionada.")
			#Enviamos el grado y la materia seleccionada para seguir la seleccion del cuestionario			
			return redirect(url_for('.select_test', select_grade=select_grade, matter=matter))
	

	return render_template('game/matter.html', title="Seleccionar grado", form=form)

'''
página para seleccionar El cuestionario a jugar
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/<select_grade>/<matter>', methods=['GET', 'POST'])
@login_required
def select_test(select_grade, matter):

	form = ChoiceTestForm(request.form)
	#Llenamos el SelectField del form con un for que recorrera un query con todos los cuestionarios que tengan en comun el grado y materia seleccionada previamente
	form.tests.choices = [(t.id_test, t.name_test) for t in Test.query.filter_by(grade_test = select_grade, matter_test=matter).all()]

	if request.method == 'POST':
		if form.validate():
			test_id = form.tests.data #la data del campo regresa el id del cuestionario

			#Primero lo transformamos a una cadena de texto
			test_id_str = str(test_id)
			#Luego obtenemos solo los numeros con la funcion re:
			id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', test_id_str)]

			test = Test.query.get_or_404(id_int)
			select_test = test.id_test #Obtenemos el id del cuestionario que finalmente es el escogido
			flash("Cuestionario seleccionado.")
			#Enviamos el id en formato int (id_int)			
			return redirect(url_for('.game_start', id_int=id_int))
	

	return render_template('game/test.html', title="Seleccionar Cuestionario", form=form)

'''
página para completar algunas configuraciones antes de empezar el juego
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/start', methods=['POST', 'GET'])
@login_required
def game_start():

	form = StartForm(request.form) #Formulario para ingresar el nombre de los dos jugadores, segundos para contestar las preguntass y el tema a jugar
	
	mode = session.get('mode', None) #Obtenemos el modo de juego escogido

	id_test = request.args.get("id_int") #Obtenemos el id del test a jugar
	quests = Quest.query.filter_by(test_id = id_test).all() #Obtenemos la lista de preguntas del test a traves de un query
	test = Test.query.get_or_404(id_test)

	name = test.name_test 
	grade = test.grade_test 
	matter = test.matter_test

	#Primero lo transformamos a una cadena de texto todas las ids de las preguntas
	quests = str(quests)
	#Luego obtenemos solo los numeros con la funcion re:
	for i in quests:
		quests_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', quests)] 

	random.shuffle(quests_int) #Desordenamos la lista de preguntas del cuestionario.

	if request.method == 'POST':
		if form.validate():

			session['test_random'] = quests_int #Guardamos la lista de ids desordenada con la funcion session
			
			#Inicialisamos algunos datos recurrentes para la jugabilidad
			# contador de preguntas, puntajes y nombres de los jugadores; tiempo en segundos del reloj
			counter = 0 
			score1 = 0
			score2 = 0
			player1 = form.player1.data
			player1 = player1.upper()
			player2 = form.player2.data
			player2 = player2.upper()
			time = form.time.data
			
			
			#Seleccion del Tema dependiendo el boton, guardamos la eleccion con session.
			#Y mandamos los datos necesarios para cada pantalla con tema diferente
			if request.form['button'] == 'tema1':
				session['theme'] = 1
				if mode == 1:
					return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
				elif mode ==2:
					return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
					
			elif request.form['button'] == 'tema2':
				session['theme'] = 2
				if mode == 1:
					return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
				elif mode ==2:
					return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
	
				
			elif request.form['button'] == 'tema3':
				session['theme'] = 3
				if mode == 1:
					return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
				elif mode ==2:
					return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
	

				

	return render_template('game/start.html', title="Juego", name=name, matter=matter, grade=grade, id_test=id_test, form=form)

'''
página donde se controlaran los datos mientras se juega el cuestionario y mostrara el resultado final
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/play', methods=['POST','GET'])
@login_required
def play():
	
	test_random = session.get('test_random', None) #Obtenemos con session el listado de ids de las preguntas desordenadas
	
	test_len = len(test_random) #Obtenemos el numero total de preguntas del cuestioanrio que se esta jugando

	counter = request.args.get("counter") #Contador que lleva cuantas preguntas se van jugando
	counter = int(counter)
	#Punteos:
	score1 = request.args.get("score1") 
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)
	#Nombre de los jugadores:
	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	#Tiempo del temporizador:
	time = request.args.get("time")
	

	if counter != test_len: 
		position = counter #position nos ayuda a obtener la pregunta que corresponde
		counter = counter + 1 
		current_question = Quest.query.filter_by(id_quest = test_random[position]).first() #obtenemos la pregunta que corresponde
		question = current_question.quest #obtenemos el campo pregunta
		answer = current_question.answer #obtenemos el campo respuesta

		#Las guardamos con session
		session['answer'] = answer
		session['question'] = question

		#Obtenemos el tema seleccionado (1, 2, 3)
		theme = session.get('theme', None)

		if theme == 1:
			return redirect(url_for('.playing', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
		elif theme == 2:
			return redirect(url_for('.playing2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
		elif theme == 3:
			return redirect(url_for('.playing3', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	#Gestion del Resultado Final
	result = ''	
	if score1 < score2:
		result = player2
		text = "La victoria es para:" 
	elif score2 < score1:
		result = player1
		text = "La victoria es para:" 
	else:
		result = "Empate"
		text = "El resultado es:" 



	return render_template('game/winner.html', title="Ganador",result=result, text=text)

'''
página donde se juega el cuestionario con el Tema1
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/playing', methods=['POST','GET'])
@login_required
def playing():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	
	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	time = request.args.get("time")
	
	question = session.get('question', None)
	answer = session.get('answer', None)
	player = ''

	#Saber el turno del jugador con la ayuda de counter:
	if counter % 2 == 0:
		player = 2
	else:
		player = 1

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if counter % 2 == 0:
				score2 = score2 + 1
			else:
				score1 = score1 + 1
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		elif request.form['boton'] == 'btn2':
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	return render_template('game/children_playing.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player = player, player1=player1, player2=player2, time=time)

'''
página donde se juega el cuestionario con el Tema2
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/playing2', methods=['POST','GET'])
@login_required
def playing2():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	
	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	time = request.args.get("time")

	question = session.get('question', None)
	answer = session.get('answer', None)
	player = ''

	#Saber el turno del jugador con la ayuda de counter:
	if counter % 2 == 0:
		player = 2
	else:
		player = 1

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if counter % 2 == 0:
				score2 = score2 + 1
			else:
				score1 = score1 + 1
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		elif request.form['boton'] == 'btn2':
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	return render_template('game/teen_playing.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player = player, player1=player1, player2=player2, time=time)

'''
página donde se juega el cuestionario con el Tema3
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/playing3', methods=['POST','GET'])
@login_required
def playing3():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	
	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	time = request.args.get("time")

	question = session.get('question', None)
	answer = session.get('answer', None)
	player = ''

	#Saber el turno del jugador con la ayuda de counter:
	if counter % 2 == 0:
		player = 2
	else:
		player = 1

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if counter % 2 == 0:
				score2 = score2 + 1
			else:
				score1 = score1 + 1
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		elif request.form['boton'] == 'btn2':
			print("Incorrecto!")
			return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	return render_template('game/college_playing.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player = player, player1=player1, player2=player2, time=time)



@page.route('/game/play2', methods=['POST','GET'])
@login_required
def play2():

	test_random = session.get('test_random', None)
	test_len = len(test_random)

	counter = request.args.get("counter") #Contador que lleva cuantas preguntas se van jugando
	counter = int(counter)
	session['counter'] = counter
	#Punteos:
	score1 = request.args.get("score1") 
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)
	session['score1'] = score1 
	session['score2'] = score2 

	#Nombre de los jugadores:
	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	session['player1'] = player1 
	session['player2'] = player2 
	#Tiempo del temporizador:
	time = request.args.get("time")
	session['time'] = time 

	if counter != test_len: 
		position = counter #position nos ayuda a obtener la pregunta que corresponde
		counter = counter + 1 
		current_question = Quest.query.filter_by(id_quest = test_random[position]).first() #obtenemos la pregunta que corresponde
		question = current_question.quest #obtenemos el campo pregunta
		answer = current_question.answer #obtenemos el campo respuesta

		#Las guardamos con session
		session['answer'] = answer
		session['question'] = question
		#Obtenemos el tema seleccionado (1, 2, 3)
		theme = session.get('theme', None)
		
		if theme == 1:
			return redirect(url_for('.key1', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
		elif theme ==2:
			return redirect(url_for('.key2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
		elif theme ==3:
			return redirect(url_for('.key3', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	result = ''	
	if score1 < score2:
		result = player2
		text = "La victoria es para:" 
	elif score2 < score1:
		result = player1
		text = "La victoria es para:" 
	else:
		result = "Empate"
		text = "El resultado es:" 

	return render_template('/game/winner.html', title="Ganador",result=result, text=text)


@page.route('/game/key1', methods=['POST','GET'])
@login_required
def key1():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	session['counter'] = counter

	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)
	session['score1'] = score1
	session['score2'] = score2

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	session['player1'] = player1
	session['player2'] = player2
	time = request.args.get("time")
	session['time'] = time
	
	question = session.get('question', None)
	answer = session.get('answer', None)
	
	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	
	return render_template('game/mode2/key1.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time)

@page.route('/game/key2', methods=['POST','GET'])
@login_required
def key2():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	session['counter'] = counter

	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)
	session['score1'] = score1
	session['score2'] = score2

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	session['player1'] = player1
	session['player2'] = player2
	time = request.args.get("time")
	session['time'] = time
	
	question = session.get('question', None)
	answer = session.get('answer', None)
	
	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	
	return render_template('game/mode2/key2.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time)


@page.route('/game/key3', methods=['POST','GET'])
@login_required
def key3():

	#variables y demás son explicadas en "def play()"
	counter = request.args.get("counter")
	counter = int(counter)
	session['counter'] = counter

	score1 = request.args.get("score1")
	score2 = request.args.get("score2")
	score1 = int(score1)
	score2 = int(score2)
	session['score1'] = score1
	session['score2'] = score2

	player1 = request.args.get("player1")
	player2 = request.args.get("player2")
	session['player1'] = player1
	session['player2'] = player2
	time = request.args.get("time")
	session['time'] = time
	
	question = session.get('question', None)
	answer = session.get('answer', None)
	
	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

	
	return render_template('game/mode2/key3.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time)




@page.route('/game/answer1', methods=['POST','GET'])
@login_required
def answer1():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/answer1.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)


@page.route('/game/answer2', methods=['POST','GET'])
@login_required
def answer2():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/answer2.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)

@page.route('/game/answer3', methods=['POST','GET'])
@login_required
def answer3():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/answer3.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)


@page.route('/game/steal1', methods=['POST','GET'])
@login_required
def steal1():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/steal1.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)

@page.route('/game/steal2', methods=['POST','GET'])
@login_required
def steal2():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/steal2.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)

@page.route('/game/steal3', methods=['POST','GET'])
@login_required
def steal3():
	question = session.get('question', None)
	answer = session.get('answer', None)
	counter = session.get('counter', None)
	score1 = session.get('score1', None)
	score2 = session.get('score2', None)
	player1 = session.get('player1', None)
	player2 = session.get('player2', None)
	time = session.get('time', None)
	player = request.args.get("player")
	player = int(player)

	if request.method == 'POST':
		if request.form['boton'] == 'btn1':
			if player == 1:
				score1 = score1 + 1
			elif player == 2:
				score2 = score2 + 1

			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

		
		elif request.form['boton'] == 'btn3':
			return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))


	return render_template('game/mode2/steal3.html', title="Inkano",question=question, answer=answer, score1=score1, score2=score2, player1=player1, player2=player2, time=time, player=player)




@page.route('/about_us')
def about_us():
	
	return render_template('/about/about.html')


@page.route('/help')
def help():
	
	return render_template('/about/help.html')

@page.route('/credits')
def credits():
	
	return render_template('/about/credits.html')

@page.route('/keyboard')
def keyboard():
	
	return render_template('/game/mode2/keyboard.html')
