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
        return template("index.html", user=curuser[0], click = False, napaka = None)

@post("/index/")
def kartoteka():
    # iz vpsanega osebaID vrni tabelo diagnoz te osebe, razvrscene po datumu
    ID = request.forms.ID
    curuser = get_user()
    c = baza.cursor()
    if ID != '':
        if request.forms.podrobno == 'podrobno':
            c.execute("""SELECT DISTINCT pregled.datum, test.ime, bolezen.ime, zdravilo.ime, zdravnik.ime, zdravnik.priimek, pregled.izvid FROM pregled
                         JOIN test ON pregled.testZdaj = test.testID
                         JOIN oseba ON pregled.oseba = oseba.osebaID
                         JOIN diagnoza 
                         JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                         JOIN zdravilo ON diagnoza.zdravilo = zdravilo.zdraviloID
                         JOIN zdravnik ON diagnoza.zdravnik = zdravnik.zdravnikID
                         ON pregled.diagnoza = diagnoza.diagnozaID
                         WHERE oseba.osebaID = %s
                         ORDER BY pregled.datum""",
                      [ID])

        else:
            c.execute("""SELECT DISTINCT pregled.datum, bolezen.ime  FROM pregled
                        JOIN oseba ON pregled.oseba = oseba.osebaID
                        JOIN diagnoza
                        JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                        ON pregled.diagnoza = diagnoza.diagnozaID
                        WHERE oseba.osebaID = %s
                        ORDER BY pregled.datum""",
                      [ID])

        d = baza.cursor()
        d.execute("""SELECT oseba.ime, oseba.priimek FROM oseba
                    WHERE oseba.osebaID = %s""",
                  [ID])
        ime_priimek = d.fetchone()
    else:
        #iz vpisanega imena, priimka in datuma rojstva vrni tabelo diagnoz te osebe, razvrščene po datumu
        ime = request.forms.ime
        priimek = request.forms.priimek
        rojstvo = request.forms.datum
        if request.forms.Podrobno:
            c.execute("""SELECT DISTINCT pregled.datum, test.ime, bolezen.ime, zdravilo.ime, zdravnik.ime, zdravnik.priimek, pregled.izvid FROM pregled
                         JOIN test ON pregled.testZdaj = test.testID
                         JOIN oseba ON pregled.oseba = oseba.osebaID
                         JOIN diagnoza 
                         JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                         JOIN zdravilo ON diagnoza.zdravilo = zdravilo.zdraviloID
                         JOIN zdravnik ON diagnoza.zdravnik = zdravnik.zdravnikID
                         ON pregled.diagnoza = diagnoza.diagnozaID
                         WHERE oseba.ime = %s AND oseba.priimek = %s AND oseba.rojstvo = %s
                         ORDER BY pregled.datum DESC""",
                      [ime, priimek, rojstvo])
        else:
            c.execute("""SELECT DISTINCT pregled.datum, bolezen.ime  FROM pregled
                        JOIN oseba ON pregled.oseba = oseba.osebaID
                        JOIN diagnoza
                        JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                        ON pregled.diagnoza = diagnoza.diagnozaID
                        WHERE oseba.ime = %s AND oseba.priimek = %s AND oseba.rojstvo = %s
                        ORDER BY pregled.datum DESC""",
                      [ime, priimek, rojstvo])
            ime_priimek = ime + ' ' + priimek
    tmp = c.fetchall()
    print(tmp)
    if len(tmp) == 0:
        # ID osebe v bazi ne obstaja
        return template("index.html", napaka="Nepravilna poizvedba, ID ne obstaja", user=curuser[0], click = False)
    else:
        return template("index.html", rows=tmp, ime_priimek = ime_priimek, click = True, napaka = None, user=curuser[0])



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


def vrni_prvi_stolpec(seznam):
    #odstrani nepotrebne znake okrog besedila
    nov = []
    for i in seznam:
        nov.append(i[0])
    return nov

@get("/index/pregled/")
def pregled():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    else:
        c = baza.cursor()
        c.execute("""SELECT ime FROM test
                    ORDER BY ime""")
        test_seznam = vrni_prvi_stolpec(c.fetchall())
        c.execute("""SELECT DISTINCT ime FROM bolezen
                    ORDER BY ime""")
        diagnoza_seznam = vrni_prvi_stolpec(c.fetchall())
        c.execute("""SELECT DISTINCT ime FROM zdravilo
                    ORDER BY ime""")
        zdravilo_seznam = vrni_prvi_stolpec(c.fetchall())
        return template("pregled.html", user=curuser[0], napaka = None,
                        test_seznam = test_seznam, diagnoza_seznam = diagnoza_seznam,
                        zdravilo_seznam=zdravilo_seznam)

@post("/index/pregled/")
def pregled_post():
    ID = request.forms.ID
    curuser = get_user()
    zdravnik = curuser[1]
    testZdaj = request.forms.testZdaj
    testNaprej = request.forms.testNaprej
    izvid = request.forms.izvid
    c = baza.cursor()
    if testNaprej != "":
        c.execute("""INSERT INTO """)
    else:
        diagnoza = request.forms.diagnoza
        zdravilo = request.forms.zdravilo




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



