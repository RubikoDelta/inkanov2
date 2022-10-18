from unicodedata import name
from flask import Flask, Blueprint, session
from flask import render_template, request, flash, redirect, url_for, abort
from flask import current_app
from flask import send_from_directory
from flask import make_response
from . import db
from flask import send_file
from flask import jsonify, json
from flask import Response
import shutil
import re, random, time
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import cast, Numeric, func, Integer, select
from .forms import LoginForm, RegisterForm, TestForm, ChoiceMatterForm, QuestForm, ChoiceGradeForm, ChoiceTestForm, StartForm 
from .models import User, Test, Quest, Image, Ans,Player
from . import login_manager
import os.path
import os
import logging
from werkzeug.utils import secure_filename
from playsound import playsound
from flask_recaptcha import ReCaptcha
from fpdf import FPDF
from . import socketio
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from app import app



page = Blueprint('page', __name__)

app.config.update({
    'RECAPTCHA_ENABLED': True,
    'RECAPTCHA_SITE_KEY': "6LcSwOogAAAAAMFUgWXJsjXefxARI1uAU0vxna__",
    'RECAPTCHA_SECRET_KEY':"6LcSwOogAAAAAEuXdWOOrhI1eAGVpqSGeDENzqya",
})

recaptcha = ReCaptcha()
recaptcha.init_app(app)
usuarios_conectados=0
#socketio = SocketIO(app)
#socketio.run(app)


#if __name__ == '__main__':
    #socketio.run(app)
#________________APARTADO DE: REGISTRO Y LOGIN DE USUARIOS____________________




""""Variables temporales para SOCKETS
-------------------------------------"""
test_randomx=[]
counterx =0
timex = 0

"""Fin variables para SOCKETS"""
@socketio.on('message')
def handleMessage(msg):
    emit('redirect', {'url': url_for('page.play',counter=0)}, broadcast=True)
    #send(User.get_by_id())

@socketio.on('index')
def limpiartabla(txt):
    return render_template('index.html', title='Index')
@page.route('/help')
def x():
    return render_template('/about/help.html')

@page.route('/game/play', methods=['POST','GET'])
@login_required
def playsockets():
    mode = request.args.get('mode')
    mode = int(mode)
    if mode == 1:
        session['mode'] = 1
        test_random = test_randomx #Obtenemos con session el listado de ids de las preguntas desordenadas
        test_len = len(test_random) #Obtenemos el numero total de preguntas del cuestioanrio que se esta jugando
        
    elif mode == 2:
        test_random = session.get('test_random', None) #Obtenemos con session el listado de ids de las preguntas desordenadas
        test_len = len(test_random) #Obtenemos el numero total de preguntas del cuestioanrio que se esta jugando

    counter = request.args.get("counter") #Contador que lleva cuantas preguntas se van jugando
    counter = int(counter)
    #Tiempo del temporizador:
    time = request.args.get("time")
    session['tiempo'] = time
    score = request.args.get("score")
    mode = session.get('mode', None)
    #if counter != test_len:
    if counter < test_len: 
        position = counter #position nos ayuda a obtener la pregunta que corresponde
        counter = counter + 1
        current_question = Quest.query.filter_by(id_quest = test_random[position]).first()
        image = Image.query.filter_by(quest_id = test_random[position]).first()
        other_ans = Ans.query.filter_by(quest_id = test_random[position]).first()
        if image:
            print('----------------')
            print(image.name)
            session['image_name'] = image.name
            #print(image.name)
        else: 
            session['image_name'] = ''
        question = current_question.quest #obtenemos el campo pregunta
        answer = current_question.answer #obtenemos el campo respuesta

        #Las guardamos con session
        session['answer'] = answer
        session['question'] = question
        #dificultad = session.get('dificultad', None)
        dificultad = request.args.get("dificultad")
        session['dificultad'] = dificultad
        #dificultad = 'Medio'
        if dificultad == 'Facil':
            lista_preguntas = [other_ans.answer1, answer]
        elif dificultad == 'Medio':
            lista_preguntas = [other_ans.answer1,other_ans.answer2, answer]
        else : 
            lista_preguntas = [other_ans.answer1,other_ans.answer2,other_ans.answer3, answer]
        
        random.shuffle(lista_preguntas)
        session['random_ans'] = lista_preguntas
        #Obtenemos el tema seleccionado (1, 2, 3)
        theme = session.get('theme', None)
        return redirect(url_for('.playing', counter=counter, player=current_user, time=time))
        if theme == 1:
            #return redirect(url_for('.playing', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
            return redirect(url_for('.playing', counter=counter, score1=0, score2=0, player1=0, player2=0, time=time))
        elif theme == 2:
            return redirect(url_for('.playing2', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
        elif theme == 3:
            return redirect(url_for('.playing3', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))

    return redirect(url_for('.chartjs'))
    if mode == 2:
        correctos = session.get('correctos', None)
        incorrectos = session.get('incorrectos', None)

        data = [
            ("Correcto", correctos),
            ("Incorrecto", incorrectos),
        ]

        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        return render_template('game/chartjs.html', title="Ganador", labels=labels, values=values)

    usuarios = Player.query.all()
    data = []
    for i in usuarios:
        data.append((i.username, i.score))
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return render_template('game/chartjs.html', title="Ganador", labels=labels, values=values)
    #return render_template('game/chartjs.html', title="Ganador",result=result, text=text, data=data)

@page.route('/game/chartjs', methods=['POST','GET'])
def chartjs():
    mode = session.get('mode', None)
    if mode == 2:
        correctos = session.get('correctos', None)
        incorrectos = session.get('incorrectos', None)
        intentos = session.get('intentos', None)
        if ((incorrectos >= correctos) and (intentos<3) ):
            restante = correctos-incorrectos
            #mensaje = "Te has quedado a " + str(restante) +" de intentos en poder aprobar "
            playagain= 0
        else: 
            playagain = 1
        data = [
            ("Correcto", correctos),
            ("Incorrecto", incorrectos),
        ]

        labels = [row[0] for row in data]
        values = [row[1] for row in data]

        if request.method == 'POST':
            #Tiempo del temporizador:
            if playagain == 1:
                return render_template('index.html', title='Index')
            time = session.get('tiempo', None)
            dificultad = session.get('dificultad', None)
            session['intentos'] = session['intentos'] +1
            session['correctos'] = session.get('correctos', None)-session.get('correctos', None)
            session['incorrectos'] = session.get('incorrectos', None) - session.get('incorrectos', None)
            return redirect(url_for('.play', counter=0, score1='score1', score2='score2',player=current_user,time=time,dificultad=dificultad,mode=2))
        return render_template('game/chartjs.html', title="Ganador", labels=labels, values=values, playagain=playagain)
    else :
        playagain= 2
        #usuarios = Player.query.all().order_by('score')
        usuarios = db.session.query(Player).order_by(Player.score.desc())
        data = []
        for i in usuarios:
            data.append((i.username, i.score))
        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        values.sort(reverse =True)
        ganador = str(values[0])
        if request.method == 'POST':
            usuarios = Player.query.all()
            for i in usuarios:
                Player.delete_players(i.username)
            return render_template('index.html', title='Index')
        return render_template('game/chartjs.html', title="Ganador", labels=labels, values=values,playagain=playagain, ganador=ganador)



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
        if recaptcha.verify():
            #llamamos desde el archivo models.py el metodo create_element con los parametros que el usario lleno en el form
            user = User.create_element(form.username.data, form.password.data, form.email.data)
            flash('Usuario registrado exitosamente!')
            return redirect(url_for('.login'))
        else:
            flash('Recaptcha Error')
            return redirect(url_for('.register'))

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
    diccionario_id_test = {}
    test_compatibles = {}
    for i in tests:
        quests = Quest.query.filter_by(test_id = i.id_test).count()
        diccionario_id_test[i.id_test] = quests
        version = Quest.get_ans(i.id_test)
        test_compatibles[i.id_test] = version
        #format_str = str(i)
        #id_int = [int(j)for j in re.findall(r'-?\d+\.?\d*', format_str)]
        #lista_id_test.append(int(id_int[0]))
    #test = Test.query.get_or_404(92)


    return render_template('test/list.html', title='Juego',
        tests=tests, pagination = pagination, page=page,
        active='tests', diccionario_id_test=diccionario_id_test, test_compatibles=test_compatibles)


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
Ruta para importar cuestionarios en formato .json
Ultima modificacion Agosto 15 de Agosto 2022 por Luis Lobos
'''
@page.route('/upload_json', methods=['GET','POST'])
@login_required
def upload_json():
    if request.method == 'POST': 
        f = request.files['file']
        #Poner aqui una condicional que verifique si el archivo es txt y pueda manipular las preguntas
        if (f.filename.find(".txt") != -1):
            extract_txt(f)
            return render_template('/upload_json.html')
        for i in range(14):
            linea = str(f.readline())
            linea = linea.replace('"','')
            linea = linea.replace('\\n\'','')
            if i == 4 :
                name = linea[35:]
            elif i == 7:
                grade = linea[34:]
            elif i == 10: 
                matter = linea[35:]
            elif i == 13:
                num = int(linea[29:])
            else:
                print('')
        test = Test.create_element(name, matter, grade, num, current_user.id)
        current_test = db.session.query(Test).order_by(Test.id_test.desc()).first() #id del test
        format_str = str(current_test)
        id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', format_str)]
        for i in range(3):
            f.readline()
        if test:
            for i in range(num):
                f.readline()
                pregunta = str(f.readline())
                pregunta = pregunta.replace('"','')
                pregunta = pregunta.replace('\\n\'','')
                pregunta = pregunta.replace(',', '')
                pregunta = pregunta[16:]
                respuesta = str(f.readline())
                respuesta = respuesta.replace('"','')
                respuesta = respuesta.replace('\\n\'','')
                respuesta = respuesta[16:]
                respuestas_alternativas=[]
                for i in range(3):
                    respuesta_al = str(f.readline())
                    respuesta_al = respuesta_al.replace('"','')
                    respuesta_al = respuesta_al.replace('\\n\'','')
                    respuesta_al = respuesta_al.replace(',','')
                    respuesta_al = respuesta_al[29:]
                    respuestas_alternativas.append(respuesta_al)
                quest = Quest.create_element(pregunta, respuesta, id_int[0])
                current_quest = Quest.query.filter_by(test_id=id_int[0]).order_by(Quest.id_quest.desc()).first()
                #id_current_quest = [int(i)for i in re.findall(r'-?\d+\.?\d*', current_quest.id_quest)] 
                id_current_quest = int(current_quest.id_quest)
                another_ans = Ans.create_element(id_current_quest, respuestas_alternativas[0], respuestas_alternativas[1],respuestas_alternativas[2])
                
                f.readline()
                if quest : 
                    print('Pregunta realizada')				
            return 'SUCCESS'			
        return "type(total_preguntas)"
    return render_template('/upload_json.html')

@page.route('/lobby')
@login_required
def lobby():
    player = Player.create_element(current_user)
    return render_template('lobby.html')


@page.route('/upload_json')
@login_required
def extract_txt(archivo):
    for i in range(4):
        linea = str(archivo.readline())
        linea = linea.replace('\\n\'','')
        if i == 0 :
            name = linea[27:]
        elif i == 1 :
            grade = linea[26:]
        elif i == 2:
            matter = linea[28:]
        elif i== 3 :
            num = int(linea[22:])
    test = Test.create_element(name, matter, grade, num, current_user.id)
    current_test = db.session.query(Test).order_by(Test.id_test.desc()).first() #id del test
    format_str = str(current_test)
    id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', format_str)]
    if test:
        for i in range(3):
            archivo.readline()
        for i in range(num):
            pregunta = str(archivo.readline())
            pregunta = pregunta[5:]
            pregunta = pregunta.replace('\\n\'','')
            respuesta = str(archivo.readline())
            respuesta = respuesta[12:]
            respuesta = respuesta.replace('\\n\'','')
            archivo.readline()
            quest = Quest.create_element(pregunta, respuesta, id_int[0])
            if quest : 
                print('Pregunta realizada')
            
'''
Ruta que muestra datos de un cuestionario específico
Última modificación Junio de 2021 por Diego Aguirre
'''
@page.route('/tests/show/<int:test_id>')
def get_test(test_id): #test_id es obtenido desde test/list.html
    print(type(test_id))
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

@page.route('/tests/finish/<int:test_id>/<int:restantes>', methods=['GET', 'POST'])
@login_required
def finish_test(test_id, restantes):

    #return render_template('/about/about.html')
    #Recibimos estos datos desde: new_test (/tests/new)
    current_test = test_id #ultimo cuestionario creado
    number_quests = restantes #número de preguntas del cuestioanrio

    form = QuestForm(request.form)

    if request.method  == 'POST':
        if form.validate():

            
            pic = request.files['pic']                        
            quest = Quest.create_element(form.quest.data, form.answer.data, current_test)
            
            flash('Pregunta creada exitosamente')
            if quest:
                current_quest = Quest.query.filter_by(test_id=test_id).order_by(Quest.id_quest.desc()).first()
                #id_current_quest = [int(i)for i in re.findall(r'-?\d+\.?\d*', current_quest.id_quest)] 
                id_current_quest = int(current_quest.id_quest)
                if pic :
                    filename = secure_filename(pic.filename)
                    basedir = os.path.abspath(os.path.dirname(__file__))
                    pic.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
                    Image.create_element(quest_id= id_current_quest, name=filename)
                if number_quests != 1: #sirve para controlar la creacion de preguntas 
                    number_quests = number_quests - 1 #Con cada pregunta creada se baja el numero de preguntas pendienetes                    
                    return redirect(url_for('.new_quest', current_test=current_test, number_quests=number_quests))

                else: 
                    return redirect(url_for('.tests'))

    return redirect(url_for('.new_quest', current_test=current_test, number_quests=number_quests))
    return redirect(url_for('.tests'))        
    #return render_template('quest/new.html', title='Crear Preguntas', form=form, id_int=id_int)
    return render_template('quest/new.html', title='Terminar cuestionario', form=form, id_int=id_int)

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
    

    ids_test = str(test)	#Primero lo transformamos a una cadena de texto
    
    id_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', ids_test)] #Luego obtenemos solo los numeros con la funcion re

    quests = Quest.query.filter_by(test_id=id_int).all() #Objeto query con la lista de las ids de todas la preguntas del cuestionario
    quests = str(quests)
    #Luego obtenemos solo los numeros con la funcion re:
    for i in quests:
        #Pendiente poder remover las imagenes cuando se elimina el cuestionario
        quests_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', quests)] 
        image = Image.query.filter_by(quest_id = quests_int)
        if image:
            print('******')
            #os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.name))
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

@page.route('/test/download_pdf/<int:test_id>')
@login_required
def download_pdf(test_id):
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
    pdf = FPDF()
 
    # Add a page
    pdf.add_page()
 
    # set style and size of font
    # that you want in the pdf
    pdf.set_font("Arial", size = 15)
 
    # create a cell
    pdf.cell(200, 10, txt = 'Nombre del Cuestionario: ' +  name,
         ln = 1, align = 'L')
    pdf.cell(200, 10, txt = 'Grado del Cuestionario: ' + grade,
        ln=1, align = 'L')
    pdf.cell(200, 10, txt = 'Materia del Cuestionario: ' + matter,
        ln = 1, align = 'L')
    pdf.cell(200, 10, txt = 'Total de preguntas: ' + number_str,
        ln = 1, align = 'L')
    pdf.cell(200, 10, txt = 'Preguntas:',
        ln = 1, align = 'L')
    
    while position <= number - 1:
        num_str = str(num)
        current_question = Quest.query.filter_by(id_quest = quests_int[position]).first() #obtenemos la pregunta que corresponde
        question = current_question.quest #obtenemos el campo pregunta
        answer = current_question.answer #obtenemos el campo respuesta
        pdf.cell(200, 10, txt = num_str+') '+ question,
            ln = 1, align = 'L')
        pdf.cell(200, 10, txt = 'Respuesta:' + answer,
            ln = 1, align = 'L')
        position = position +1
        num=num+1
    
        

    pdf.output("HOLA.pdf")
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename=name + '.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response
    #return send_file(pdf.output("GFG.pdf"), as_attachment=True)

@page.route('/test/download_json/<int:test_id>')
@login_required
def download_json(test_id):
    test = Test.query.get_or_404(test_id) #Declaramos un objeto con la id del cuestionario para eliminar
    name = test.name_test
    grade = test.grade_test
    matter = test.matter_test
    number = test.number_test
    number_str = str(number)
    quests = Quest.query.filter_by(test_id = test_id).all()
    quests = str(quests)
    for i in quests:
        quests_int = [int(i)for i in re.findall(r'-?\d+\.?\d*', quests)]

    position = 0
    num = 1

    if test.user_id != current_user.id:
        abort(404)

    preguntasList = [] # lista
    mi_encabezado = {"Encabezado": [{"Nombre del Cuestionario": name}, {"Grado del cuestionario": grade}, {"Materia del Cuestionario": matter}, {"Total de preguntas": number_str}]}
    preguntasList.append(mi_encabezado)
    while position <= number - 1:
        num_str = str(num)
        current_question = Quest.query.filter_by(id_quest = quests_int[position]).first() #obtenemos la pregunta que corresponde
        question = current_question.quest #obtenemos el campo pregunta
        answer = current_question.answer #obtenemos el campo respuesta
        mi_respuesta = {"Pregunta": question,'Respuesta': answer}
        preguntasList.append(mi_respuesta)
        position = position +1
        num=num+1

    filejson = jsonify(preguntasList)
    filejson.headers['Content-Disposition'] = 'attachment;filename='+name+'.json' 
    return filejson
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

            
            pic = request.files['pic']
            
            
            quest = Quest.create_element(form.quest.data, form.answer.data, id_int[0])
            
            flash('Pregunta creada exitosamente')
            if quest:
                current_quest = Quest.query.filter_by(test_id=id_int[0]).order_by(Quest.id_quest.desc()).first()
                #id_current_quest = [int(i)for i in re.findall(r'-?\d+\.?\d*', current_quest.id_quest)] 
                id_current_quest = int(current_quest.id_quest)
                another_ans = Ans.create_element(id_current_quest, form.answer1.data, form.answer2.data,form.answer3.data)

                if pic :
                    filename = secure_filename(pic.filename)
                    basedir = os.path.abspath(os.path.dirname(__file__))
                    pic.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
                    Image.create_element(quest_id= id_current_quest, name=filename)
                if number_quests != 1: #sirve para controlar la creacion de preguntas 
                    number_quests = number_quests - 1 #Con cada pregunta creada se baja el numero de preguntas pendienetes

                    
                    
                    #En el return usamos recursividad hacia esta misma clase:
                    #Se manda nuevamente el cuestionario actual (current_test) y preguntas pedientes -1 (number_quests) 
                    

                    return redirect(url_for('.new_quest', current_test=current_test, number_quests=number_quests))

                else: 
                    return redirect(url_for('.tests'))
            
    return render_template('quest/new.html', title='Crear Preguntas', form=form, id_int=id_int)
 

@app.route('/<int:id>')
def get_img(id):
    #usar aqui un decode
    img = Image.query.filter_by(id=id).first()
    
    cadena = img.img.encode('UTF-8')
    emoji = '😂'.encode('UTF-8')
    print('-----------------------')
    print(emoji)
    if not img:
        return 'Img Not Found!', 404

    return Response(img.img, mimetype=img.mimetype)
'''
@page.route('/uploadimage', methods=['POST'])
def uploadimg():				
    pic = request.files['pic']

    if not pic:
        return 'No pic uploaded', 400
    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype
    img = Image(img=pic.read(), mimetype = mimetype, name=filename)
    db.session.add(img)
    db.session.commit()

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
        
        another_ans = Ans.create_element(quest.id_quest, form.answer1.data, form.answer2.data,form.answer3.data)
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
            #dificultad = form.dificultad.data
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
    elecciones = []
    #Llenamos el SelectField del form con un for que recorrera un query con todos los cuestionarios que tengan en comun el grado y materia seleccionada previamente
    tests = Test.query.filter_by(grade_test = select_grade, matter_test=matter).all()
    for i in tests:
        count = Quest.get_ans(i.id_test)
        if count == True: 
            elecciones.append(i)
    form.tests.choices = [(t.id_test, t.name_test) for t in elecciones]
    #form.tests.choices = [(t.id_test, t.name_test) for t in Test.query.filter_by(grade_test = select_grade, matter_test=matter).all()]

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
            session['dificultad'] = form.dificultad.data
            
            listausuarios = []

            
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
    dificultad = session.get('dificultad', None)
    listausuarios  = session.get('listausuarios', None)
    if dificultad == 'Facil':
        form.time.choices = [(t, str(t)) for t in range(5,31,5)]
    elif dificultad == 'Medio': 
        form.time.choices = [(t, str(t)) for t in range(5,16,5)]
    else : 
        form.time.choices = [(5,'5')]
    
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
            #player1 = form.player1.data
            #player1 = player1.upper()
            #player2 = form.player2.data
            #player2 = player2.upper()
            time = form.time.data
            
            #Seleccion del Tema dependiendo el boton, guardamos la eleccion con session.
            #Y mandamos los datos necesarios para cada pantalla con tema diferente
            if request.form['button'] == 'tema1':
                session['theme'] = 1
                if mode == 1:
                    test_randomx.clear()
                    test_randomx.extend(quests_int)
                    socketio.emit('iniciar', {'url': url_for('page.play',counter=0, time=time, dificultad=dificultad,score=0, mode=1)}, broadcast=True)
                    return redirect(url_for('.index'))
                    #return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
                elif mode ==2:
                    session['correctos'] = 0
                    session['incorrectos'] = 0
                    session['intentos'] = 0
                    return redirect(url_for('.play', counter=counter, player=current_user, time=time,dificultad=dificultad,mode=2))
                    
            elif request.form['button'] == 'tema2':
                session['theme'] = 2
                return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2,time=time,dificultad=dificultad))
                if mode == 1:
                    return redirect(url_for('.play', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
                elif mode ==2:
                    print("HOLA")
                    
    
                
            elif request.form['button'] == 'tema3':
                session['theme'] = 3
                if mode == 1:
                    return redirect(url_for('.play', counter=counter, score1=score1, score2=score2,time=time))
                elif mode ==2:
                    return redirect(url_for('.play2', counter=counter, score1=score1, score2=score2,time=time))
    

                
    usuarios = Player.query.all()
    for i in usuarios:
        i.update_score(i.username,0)
    return render_template('game/start.html', title="Juego", name=name, matter=matter, grade=grade, id_test=id_test,usuarios=usuarios, form=form)

'''
página donde se controlaran los datos mientras se juega el cuestionario y mostrara el resultado final
Última modificación Agosto de 2021 por Diego Aguirre
'''
@page.route('/game/play', methods=['POST','GET'])
@login_required
def play():
    
    test_random = session.get('test_random', None) #Obtenemos con session el listado de ids de las preguntas desordenadas
    test_len = len(test_random) #Obtenemos el numero total de preguntas del cuestioanrio que se esta jugando
 
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

    #if counter != test_len:
    if counter < test_len: 
        position = counter #position nos ayuda a obtener la pregunta que corresponde
        counter = counter + 1 
        current_question = Quest.query.filter_by(id_quest = test_random[position]).first()
        image = Image.query.filter_by(quest_id = test_random[position]).first()
        other_ans = Ans.query.filter_by(quest_id = test_random[position]).first()
        if image:
            session['image_name'] = image.name
            #print(image.name)
        else: 
            session['image_name'] = ''
        question = current_question.quest #obtenemos el campo pregunta
        answer = current_question.answer #obtenemos el campo respuesta

        #Las guardamos con session
        session['answer'] = answer
        session['question'] = question
        dificultad = request.args.get("dificultad")

        if dificultad == 'Facil':
            lista_preguntas = [other_ans.answer1, answer]
        elif dificultad == 'Medio':
            lista_preguntas = [other_ans.answer1,other_ans.answer2, answer]
        else : 
            lista_preguntas = [other_ans.answer1,other_ans.answer2,other_ans.answer3, answer]
        
        random.shuffle(lista_preguntas)
        session['random_ans'] = lista_preguntas
        #Obtenemos el tema seleccionado (1, 2, 3)
        theme = session.get('theme', None)

        if theme == 1:
            #return redirect(url_for('.playing', counter=counter, score1=score1, score2=score2, player1=player1, player2=player2, time=time))
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

    #data = {' Jugador' : 'Puntuacion', player1: score1, player2: score2}

    data = [
        (player1, score1),
        (player2, score2),
    ]

    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    return render_template('game/chartjs.html', title="Ganador", labels=labels, values=values)
    #return render_template('game/chartjs.html', title="Ganador",result=result, text=text, data=data)

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
    mode = session.get('mode', None)
    """score1 = request.args.get("score1")
    score2 = request.args.get("score2")
    score1 = int(score1)
    score2 = int(score2)"""
    time = request.args.get("time")

    question = session.get('question', None)
    answer = session.get('answer', None)
    image = session.get('image_name', None)
    dificultad = session.get('dificultad', None)
    player = ''
    temporizador = session.get("data-value")
    random_ans = session.get('random_ans', None)
    '''ans1 = session.get('ans1', None)
    ans2 = session.get('ans2', None)
    ans3 = session.get('ans2', None)'''

    #Saber el turno del jugador con la ayuda de counter:
    if counter % 2 == 0:
        player = 2
    else:
        player = 1
    if request.method == 'POST':
        print("-----------------")
        print(request.form['boton'])
        if request.form['boton'] == answer:
            if mode == 2 :
                session['correctos'] = session.get('correctos', None)+1 
                return redirect(url_for('.play', counter=counter, player=current_user, time=time,dificultad=dificultad, mode=2))
            socketio.emit('redirect', {'url': url_for('page.play',counter=counter, time=time, dificultad=dificultad, mode=1)}, broadcast=True)
            jugador = Player.get_by_username(str(current_user))
            print(current_user)
            if jugador: 
                print(jugador.score)
                puntuacion = jugador.score+1+ int(request.form['temporizador'])
                Player.update_score(jugador.username,puntuacion)
                
            else: 
                print("Jugador no encontrado")
            #playsound('/home/luis/Documents/practica_final/Inkano/inknaof/app/correcto.mp3')
            
            stoptime()
            return redirect(url_for('.play', counter=counter, time=time,dificultad=dificultad, mode=1))

        else:
            if mode == 2 :
                session['incorrectos'] = session.get('incorrectos', None)+1 
                return redirect(url_for('.play', counter=counter,player=current_user, time=time,dificultad=dificultad, mode=2))
            socketio.emit('redirect', {'url': url_for('page.play', counter=counter, time=time, dificultad=dificultad, mode=1)}, broadcast=True)
            #playsound('/home/luis/Documents/practica_final/Inkano/inknaof/app/incorrecto.mp3')
            return redirect(url_for('.play', counter=counter,time=time, dificultad=dificultad, mode=1))

    if dificultad == 'Facil':
        if not image:
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[1], ans1=random_ans[0],verdadera=answer,
            player = current_user,time=time, image='error',dificultad=dificultad)
        else: 
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[1], ans1=random_ans[0],
            player = current_user,time=time,image=image, dificultad=dificultad)
    elif dificultad == 'Medio':
        if not image:
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[2], ans1=random_ans[0],ans2=random_ans[1],verdadera=answer,
            player = current_user,time=time, image='error',dificultad=dificultad)
        else: 
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[2], ans1=random_ans[0],ans2=random_ans[1],verdadera=answer,
             player = current_user,time=time,image=image, dificultad=dificultad)
    else:
        if not image:
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[3], ans1=random_ans[0],ans2=random_ans[1], ans3=random_ans[2],
            player = current_user,time=time, image='error',dificultad=dificultad)
        else: 
            return render_template('game/children_playing.html', title="Inkano",question=question, answer=random_ans[3], ans1=random_ans[0],ans2=random_ans[1], ans3=random_ans[2],
            player = current_user,time=time,image=image, dificultad=dificultad)


'''
página donde se juega el cuestionario con el Tema2
Última modificación Agosto de 2021 por Diego Aguirre
'''

def stoptime():
    time.sleep(5)

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
                score2 = score2 + 3
            else:
                score1 = score1 + 3
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
                score2 = score2 + 3
            else:
                score1 = score1 + 3
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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
                score1 = score1 + 2
            elif player == 2:
                score2 = score2 + 2

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
