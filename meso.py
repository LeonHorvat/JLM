from bottle import *
import auth_public as auth
import psycopg2, psycopg2.extensions, psycopg2.extras
import hashlib

################
#priklop na bazo
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

################
#test priklopa na bazo
def test(posta):
    cur.execute('''
                    SELECT * FROM uporabnik WHERE username=%s
                ''', [posta])
    return (cur.fetchone())

print(test('sgalea0'))


#zdravnik testni zajcek
#username: sgalea0
#password: wXNoal


#raziskovalec testni zajcek
#username: rdollarh
#password: 7t6rIU


################
#bottle uvod, pomozne funkcije
static_dir = "./static"
secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"

def pooblastilo(user):
    c = baza.cursor()
    c.execute("SELECT pooblastilo FROM uporabnik WHERE username=%s",
              [user])
    r = c.fetchone()[0]
    c.close()
    return r


def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def get_user(auto_login = True, auto_redir=False):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Ce ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piskotka
    username = request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        #Ce uporabnik ze prijavljen, nima smisla, da je na route login
        if auto_redir:
            redirect('/index/')
        else:
            c = baza.cursor()
            c.execute("SELECT username FROM uporabnik WHERE username=%s",
					  [username])
            r = c.fetchone()
            c.close ()
            if r is not None:
                # uporabnik obstaja, vrnemo njegove podatke
                return r
    # Ce pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/login/')
    else:
        return None

@route("/static/<filename:path>")
def static(filename):
    """Splosna funkcija, ki servira vse staticne datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)


################
#bottle routes
@get("/login/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("login.html",
                           napaka=None,
                           username=None)

@post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabnisko ime, ki ga je uporabnik vpisal v formo
    username = request.forms.username
    # Izracunamo MD5 has gesla, ki ga bomo spravili
    password = password_md5(request.forms.password)
    # Preverimo, ali se je uporabnik pravilno prijavil
    c = baza.cursor()
    c.execute("SELECT * FROM uporabnik WHERE username=%s AND hash=%s",
              [username, password])
    tmp = c.fetchone()
    if tmp is None:
        # Username in geslo se ne ujemata
        return template("login.html",
                               napaka="Nepravilna prijava",
                               username=username)
    else:
        response.set_cookie('username', username, path='/', secret=secret)
        if tmp[2] == 'zdravnik':
            redirect('/index/')
        elif tmp[2] == 'raziskovalec':
            redirect("/indexraziskovalec/")
        else:
            redirect("/indexdirektor/")


    # else:
    #     # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
    #     response.set_cookie('username', username, path='/', secret=secret)
    #     redirect("/index/")

@get("/logout/")
def logout():
    """Pobrisi cookie in preusmeri na login."""
    response.delete_cookie('username', path='/', secret=secret)
    #print(get_user())
    redirect('/login/')

@get("/index/")
def index():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    else:
        return template("index.html", user=curuser[0], click = False)

@post("/index/")
def kartoteka():
    # iz vpsanega osebaID vrni tabelo diagnoz te osebe, razvrscene po datumu
    ID = request.forms.ID
    curuser = get_user()
    c = baza.cursor()
    c.execute("""SELECT DISTINCT pregled.datum, bolezen.ime  FROM pregled
                JOIN oseba ON pregled.oseba = oseba.osebaID
                JOIN diagnoza
                JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                ON pregled.diagnoza = diagnoza.diagnozaID
                WHERE oseba.osebaID = %s
                ORDER BY pregled.datum DESC""",
              [ID])
    tmp = c.fetchall()
    if tmp is None:
        # ID osebe v bazi ne obstaja
        return template("index.html", napaka="Nepravilna poizvedba")
    if tmp is not None:
        return template("index.html", rows=tmp, click = True, napaka = None, user=curuser[0])



@get("/indexdirektor/")
def index_direktor():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    else:
        return template("indexdirektor.html", user=curuser[0])

@get("/indexraziskovalec/")
def index_direktor():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    else:
        return template("indexraziskovalec.html", user=curuser[0])

@get("/index/messenger/")
def messenger():
    '''Servira stran (na novi routi) z vsemi sporocili, tudi z vstavljanjem'''
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    c = baza.cursor()
    c.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = c.fetchall()
    c1 = baza.cursor()
    c1.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = c1.fetchall()
    return template("messenger.html", rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka=None)
    #return template("messenger.html", user=curuser[0])

@post("/index/messenger/")
def novo_sporocilo():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    prejID = request.forms.get('prejID')
    sporocilo = request.forms.get('sporocilo')
    curuser = get_user()
    c = baza.cursor()
    c.execute("""INSERT INTO sporocila (posiljatelj, prejemnik, vsebina)
                VALUES (%s, %s, %s)""",
              [curuser[0], prejID, sporocilo])
    redirect('/index/messenger/')

run(host='localhost', port=8080)



