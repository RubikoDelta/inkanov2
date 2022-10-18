$(document).ready(function() {
    
    const lobby = io()
    const start = io('/start')
    const socket = io('/about_us');

    //socket.emit('admin', 'HOLA A TODOS')
    
    $('#send').on('click', function () {
        lobby.emit('message', 'Welcome')
        window.location.href = "http://127.0.0.1:5000/";
		
        //socket.disconnect()
        
        
	})

    lobby.on('iniciar', function (data){
        window.location = data.url;
    });

    lobby.on('redirect', function(data) {
        window.FlashMessage.success('Siguiente pregunta', {
            timeout: 3000,
            container: '.flash-container',
            progress: true
        });
        document.getElementById("temporizador").style.opacity = "0";
        document.getElementById("botones").style.opacity = "0";
        document.getElementById("respuesta").style.opacity = "1";
        setTimeout(function() {window.location = data.url;}, 5000);
        
    });

    lobby.on('message', function(data) {
        window.location = data.url
    });

    $('#respuesta').on('click', function () {
        //var elem = document.getElementById('respuesta');
        //var txt = elem.textContent
        lobby.emit('respuesta', 'Welcome', broadcast=True);
		
        //socket.disconnect()
        
        
	})

    lobby.on('respuesta', function(){
        window.FlashMessage.success('Message bag #1');
        alert("I am an alert box!");
        console.log('HOLA');
        /*new window.FlashMessage(
            "Siguiente pregunta",
            "success",
            {
              timeout: "20000",
              progress: true,
              // thumb: 'https://pbs.twimg.com/profile_images/659436766420672512/-pS2Bgfl.jpg'
            }
        )*/
    })

    $('home').on('click', function() {
        lobby.emit('index', '')
        window.location.href = "http://127.0.0.1:5000/";

    })
    //console.log(typeof lobby)
    /*Object.keys(lobby).forEach((prop)=> console.log(prop));
    console.log("-------------")
    Object.keys(lobby.json).forEach((prop)=> console.log(prop));
    console.log(typeof lobby.connected)
    console.log(typeof lobby.nsp)
    console.log(typeof lobby.json)
    console.log(typeof lobby.acks)
    console.log(typeof lobby.subs)*/


    
});


