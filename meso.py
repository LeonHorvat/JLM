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
    return (cur.fetchall())

print(test('sgalea0'))



#zdravnik testni zajcek
#username: sgalea0
#password: wXNoal


#raziskovalec testni zajcek
#username: rdollarh
#password: 7t6rIU

#direktor testni zajcek
#username: lhearse5i
#password: lbfEDb

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

print(password_md5("mat555"))

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

@get("/register/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("register.html", name=None, surname=None, institution=None, mail=None,napaka=None)

@post("/register/")
def nov_zahtevek():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    username = request.forms.get('username')
    name = request.forms.get('exampleInputName')
    surname = request.forms.get('exampleInputName')
    institution = request.forms.get('institution')
    mail = request.forms.get('exampleInputEmail1')

    #trenutno je tule mali bug, saj ce geslo vsebuje sumnik, se program zlomi
    password = password_md5(request.forms.get('exampleInputPassword1'))
    password2 = password_md5(request.forms.get('exampleConfirmPassword'))

    #preverimo, ce je izbrani username ze zaseden
    c1 = baza.cursor()
    c1.execute("SELECT * FROM uporabnik WHERE username=%s",
              [username])
    tmp = c1.fetchone()
    if tmp is not None:
        return template("register.html", name=name,
                        surname=surname, institution=institution, mail=mail, napaka="This username is already taken. Please choose another one.")

    #preverimo, ali se gesli ujemata
    if password != password2:
        return template("register.html", name=name,
                        surname=surname, institution=institution, mail=mail, napaka="Passwords do not match!")


    #ce pridemo, do sem, je vse uredu in lahko vnesemo zahtevek v bazo
    c = baza.cursor()
    c.execute("""INSERT INTO zahtevek (username, ime, priimek, ustanova, mail, hash)
                VALUES (%s, %s, %s, %s, %s, %s)""",
              [username, name, surname, institution, mail, password])
    return template("register.html", name = None,
                    surname=None, institution=None, mail=None, napaka="Request sent successfully!")

@get("/logout/")
def logout():
    """Pobrisi cookie in preusmeri na login."""
    response.delete_cookie('username', path='/', secret=secret)
    #print(get_user())
    redirect('/login/')

@get("/index/")
def index():
    curuser = get_user()
    c1 = baza.cursor()
    c1.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
    tmp1 = c1.fetchall()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    else:
        return template("index.html", rows_spor = tmp1, user=curuser[0], click = 0, napaka = None)

@post("/index/")
def kartoteka():
    # Iz vpisanega osebaID vrni tabelo diagnoz te osebe, razvrscene po datumu.
    # Ce je obkljukano podrobno, vrne tabelo pregled.
    ID = request.forms.ID
    curuser = get_user()
    c = baza.cursor()
    if ID != '':
        try:
            int(ID)
        except ValueError:
            return template("index.html", napaka="Nepravilna poizvedba, napačna oblika vnešenih podatkov.", rows_spor = None, user=curuser[0], click=0)
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
                         ORDER BY pregled.datum DESC""",
                      [ID])

        else:
            c.execute("""SELECT datum, ime FROM (
                        SELECT pregled.datum, bolezen.ime, 
                        ROW_NUMBER() OVER (PARTITION BY bolezen.ime ORDER BY pregled.datum) AS RowNumber
                        FROM pregled
                        JOIN oseba ON pregled.oseba = oseba.osebaID
                        JOIN diagnoza
                        JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                        ON pregled.diagnoza = diagnoza.diagnozaID
                        WHERE oseba.osebaID = %s)
                        AS a WHERE a.RowNumber = 1
                        ORDER BY datum DESC""",
                      [ID])

        d = baza.cursor()
        d.execute("""SELECT oseba.ime, oseba.priimek FROM oseba
                    WHERE oseba.osebaID = %s""",
                  [ID])
        ime_priimek = d.fetchone()
    else:
        #iz vpisanega imena, priimka in datuma rojstva vrni tabelo diagnoz te osebe, razvrscene po datumu
        ime = request.forms.ime
        priimek = request.forms.priimek
        rojstvo = request.forms.datum
        try:
            if request.forms.podrobno == 'podrobno':
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
                c.execute(""" SELECT datum, ime FROM (
                            SELECT pregled.datum, bolezen.ime, 
                            ROW_NUMBER() OVER (PARTITION BY bolezen.ime ORDER BY pregled.datum) AS RowNumber
                            FROM pregled
                            JOIN oseba ON pregled.oseba = oseba.osebaID
                            JOIN diagnoza
                            JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                            ON pregled.diagnoza = diagnoza.diagnozaID
                            WHERE oseba.ime = %s AND oseba.priimek = %s AND oseba.rojstvo = %s)
                            AS a WHERE   a.RowNumber = 1
                            ORDER BY datum DESC""",
                          [ime, priimek, rojstvo])
                ime_priimek = ime + ' ' + priimek
        except psycopg2.DataError:
            return template("index.html", napaka="Nepravilna poizvedba, napačna oblika vnešenih podatkov.", rows_spor = None, user=curuser[0], click=0)

    tmp = c.fetchall()
    if len(tmp) == 0:
        # ID osebe v bazi ne obstaja
        return template("index.html", napaka="Nepravilna poizvedba, ID ne obstaja", rows_spor = None, user=curuser[0], click = 0)
    elif request.forms.podrobno == 'podrobno':
        return template("index.html", rows=tmp, rows_spor=None, ime_priimek = ime_priimek, click = 2, napaka = None, user=curuser[0])
    else:
        return template("index.html", rows=tmp, rows_spor=None, ime_priimek = ime_priimek, click = 1, napaka = None, user=curuser[0])



@get("/indexdirektor/")
def index_direktor():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    else:
        c = baza.cursor()
        c.execute("""SELECT username, ime, priimek, ustanova, mail FROM zahtevek
                        WHERE zahtevek.odobreno = %s
                        ORDER BY zahtevek.datum DESC""",
                  [False])
        tmp = c.fetchall()
        c1 = baza.cursor()
        c1.execute("""SELECT username, ime, priimek, ustanova, mail FROM zahtevek
                        WHERE zahtevek.odobreno = %s
                        ORDER BY zahtevek.datum DESC""",
                  [True])
        tmp1 = c1.fetchall()
        return template("indexdirektor.html", rows=tmp, rows_p=tmp1, user=curuser[0], napaka=None)

@post("/indexdirektor/")
def index_direktor():
    if (str(request.params.type) == "zavrni"):
        c1 = baza.cursor()
        c1.execute("""DELETE FROM zahtevek
                            WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
    if (str(request.params.type) == "odobri"):
        c2 = baza.cursor()
        c2.execute("""UPDATE zahtevek SET odobreno = true
                                WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
        c3 = baza.cursor()
        c3.execute("""SELECT username, hash FROM zahtevek WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
        tmp = c3.fetchall()
        c4 = baza.cursor()
        c4.execute("""INSERT INTO uporabnik (username, hash, pooblastilo) VALUES (%s,%s,%s)""",
                   [tmp[0][0], tmp[0][1], "raziskovalec"])

    '''print(tmp)
    print(request.params.get("seznam", type=str))
    print(str(request.params.seznam))
    print(str(request.params.type) == "zavrni")'''

    redirect('/indexdirektor/')

    #TODO: sedaj lahko oznaci samo enega na enkrat (bug pri request.params.get ...), popraviti to
    #TODO: ob kliku na gumb se tabela ne posodi sama od sebe, je potrebno osveziti stran, popraviti to

@get("/indexraziskovalec/")
def index_raziskovalec():
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
        c.execute("""SELECT ime FROM test
                    JOIN specializacija ON test.testid = specializacija.test
                    WHERE zdravnik = %s
                    ORDER BY ime""",
                    [curuser[0]])

        test_seznam2 = vrni_prvi_stolpec(c.fetchall())

        c.execute("""SELECT DISTINCT ime FROM bolezen
                    ORDER BY ime""")
        diagnoza_seznam = vrni_prvi_stolpec(c.fetchall())
        c.execute("""SELECT DISTINCT ime FROM zdravilo
                    ORDER BY ime""")
        zdravilo_seznam = vrni_prvi_stolpec(c.fetchall())
        return template("pregled.html", user=curuser[0], napaka = None,
                        test_seznam = test_seznam,
                        test_seznam2=test_seznam2,diagnoza_seznam = diagnoza_seznam,
                        zdravilo_seznam=zdravilo_seznam)

@post("/index/pregled/")
def pregled_post():
    curuser = get_user()
    ID = request.forms.ID
    zdravnik = curuser[0]

    c = baza.cursor()
    c.execute("""SELECT testid FROM test
                WHERE ime = %s""",
                [request.forms.testZdaj])
    testZdaj = c.fetchone()[0]

    izvid = request.forms.izvid
    if izvid == '':
        izvid = 'NULL'
    c = baza.cursor()
    if request.forms.testNaprej != "":
        c.execute("""SELECT testid FROM test
                    WHERE ime = %s""",
                  [request.forms.testNaprej])
        testNaprej = c.fetchone()[0]
        vrstica = [ID, zdravnik, testZdaj, testNaprej, izvid]
        c.execute("""INSERT INTO pregled (oseba,zdravnik,testZdaj,testNaprej,izvid)
                    VALUES ({0},'{1}','{2}','{3}','{4}');""".format(*vrstica))
    else:
        c.execute("""SELECT bolezenid FROM bolezen
                    WHERE ime = %s""",
                  [request.forms.diagnoza])
        diagnoza = c.fetchone()[0]
        c.execute("""SELECT zdraviloid FROM zdravilo
                    WHERE ime = %s""",
                  [request.forms.zdravilo])
        zdravilo = c.fetchone()[0]
        vrstica2 = [diagnoza, zdravilo, zdravnik]
        c.execute("""INSERT INTO diagnoza(bolezen,zdravilo,zdravnik) 
                    VALUES ('{0}','{1}','{2}');""".format(*vrstica2))
        c.execute("""SELECT diagnozaid FROM diagnoza
                    ORDER BY diagnozaid DESC
                    LIMIT 1;""")
        diagnozaid = c.fetchone()[0]
        vrstica1 = [ID, zdravnik, testZdaj, 'NULL', diagnozaid, izvid]
        c.execute("""INSERT INTO pregled (oseba,zdravnik,testZdaj,testNaprej,diagnoza,izvid)
                    VALUES ({0},'{1}','{2}',{3},{4},'{5}');""".format(*vrstica1))
    redirect('/index/')



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
    c1 = baza.cursor()
    c1.execute("SELECT * FROM uporabnik WHERE username=%s",
              [prejID])
    tmp_preveri = c1.fetchone()
    c2 = baza.cursor()
    c2.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = c2.fetchall()
    c3 = baza.cursor()
    c3.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = c3.fetchall()

    if tmp_preveri is None:
        return template("messenger.html",
                               rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka="Ta prejemnik ne obstaja!")
    c = baza.cursor()
    c.execute("""INSERT INTO sporocila (posiljatelj, prejemnik, vsebina)
                VALUES (%s, %s, %s)""",
              [curuser[0], prejID, sporocilo])
    redirect('/index/messenger/')

run(host='localhost', port=8080)



