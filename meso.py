from bottle import *


static_dir = "./static"


@route("/static/<filename:path>")
def static(filename):
    """Splosna funkcija, ki servira vse staticne datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@get("/login/")
def login_get():
    """Serviraj formo za login."""
    #curuser = get_user(auto_redir = True)
    return template("login.html",
                           napaka=None,
                           logged=None,
                           username=None)

@get("/index/")
def index():
    """Serviraj formo za login."""
    #curuser = get_user(auto_redir = True)
    return template("index.html",
                           napaka=None,
                           logged=None,
                           username=None)

run(host='localhost', port=8080)
