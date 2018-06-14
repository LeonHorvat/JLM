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

#print(test('sgalea0'))



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
    cur.execute("SELECT pooblastilo FROM uporabnik WHERE username=%s",
              [user])
    r = cur.fetchone()[0]
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
    # preverimo, ali je zahtevek mogoce v cakanju
    c2 = baza.cursor()
    c2.execute("SELECT * FROM zahtevek WHERE username=%s AND hash=%s",
              [username, password])
    tmp2 = c2.fetchone()
    print(tmp2)
    if tmp is None:
        if tmp2 is None:
            return template("login.html",
                                   napaka="Nepravilna prijava",
                                   username=username)
        elif tmp2[7] == True:
            return template("login.html",
                            napaka="Nepravilna prijava",
                            username=username)
        else:
            return template("login.html",
                            napaka="Zahtevek registracije je v cakanju.",
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

@get("/forgot-password/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("forgot-password.html")

@post("/register/")
def nov_zahtevek():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    username = request.forms.username
    name = request.forms.exampleInputName
    surname = request.forms.exampleInputLastName
    institution = request.forms.institution
    mail = request.forms.exampleInputEmail1

    #trenutno je tule mali bug, saj ce geslo vsebuje sumnik, se program zlomi
    password = password_md5(request.forms.exampleInputPassword1)
    password2 = password_md5(request.forms.exampleConfirmPassword)

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
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
    tmp1 = cur.fetchall()
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
            return template("index.html", napaka="Nepravilna poizvedba, napacna oblika vnesenih podatkov.", rows_spor = None, user=curuser[0], click=0)
        if request.forms.podrobno == 'podrobno':
            c.execute("""SELECT DISTINCT pregled.datum, test.ime, bolezen.ime, zdravilo.ime, zdravnik.ime, zdravnik.priimek, pregled.izvid FROM pregled
                         JOIN test ON pregled.testZdaj = test.testID
                         JOIN oseba ON pregled.oseba = oseba.osebaID
                         FULL JOIN diagnoza 
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
                        FULL JOIN diagnoza
                        JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                        ON pregled.diagnoza = diagnoza.diagnozaID
                        WHERE oseba.osebaID = %s)
                        AS a WHERE a.RowNumber = 1
                        ORDER BY datum DESC""",
                      [ID])

        cur.execute("""SELECT oseba.ime, oseba.priimek FROM oseba
                    WHERE oseba.osebaID = %s""",
                  [ID])
        ime_priimek = cur.fetchone()
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
                             FULL JOIN diagnoza 
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
                            FULL JOIN diagnoza
                            JOIN bolezen ON diagnoza.bolezen = bolezen.bolezenID
                            ON pregled.diagnoza = diagnoza.diagnozaID
                            WHERE oseba.ime = %s AND oseba.priimek = %s AND oseba.rojstvo = %s)
                            AS a WHERE   a.RowNumber = 1
                            ORDER BY datum DESC""",
                          [ime, priimek, rojstvo])
            ime_priimek = (ime, priimek)
        except psycopg2.DataError:
            return template("index.html", napaka="Nepravilna poizvedba, napacna oblika vnesenih podatkov.", rows_spor = None, user=curuser[0], click=0)

    tmp = c.fetchall()
    c.close()
    print(ime_priimek)
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
        cur.execute("""SELECT username, ime, priimek, ustanova, mail FROM zahtevek
                        WHERE zahtevek.odobreno = %s
                        ORDER BY zahtevek.datum DESC""",
                  [False])
        tmp = cur.fetchall()
        cur.execute("""SELECT username, ime, priimek, ustanova, mail FROM zahtevek
                        WHERE zahtevek.odobreno = %s
                        ORDER BY zahtevek.datum DESC""",
                  [True])
        tmp1 = cur.fetchall()
        cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                    WHERE sporocila.prejemnik = %s
                    ORDER BY sporocila.datum DESC
                    LIMIT 3""",
                  [curuser[0]])
        tmp2 = cur.fetchall()
        return template("indexdirektor.html", rows=tmp, rows_p=tmp1, rows_spor=tmp2, user=curuser[0], napaka=None)

@post("/indexdirektor/")
def index_direktor():
    if (str(request.params.type) == "zavrni"):
        cur.execute("""DELETE FROM zahtevek
                            WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
    if (str(request.params.type) == "odobri"):
        cur.execute("""UPDATE zahtevek SET odobreno = true
                                WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
        cur.execute("""SELECT username, hash FROM zahtevek WHERE zahtevek.username = %s""",
                   [str(request.params.seznam)])
        tmp = cur.fetchall()
        cur.execute("""INSERT INTO uporabnik (username, hash, pooblastilo) VALUES (%s,%s,%s)""",
                   [tmp[0][0], tmp[0][1], "raziskovalec"])

    '''print(tmp)
    print(request.params.get("seznam", type=str))
    print(str(request.params.seznam))
    print(str(request.params.type) == "zavrni")'''

    redirect('/indexdirektor/')

    #TODO: sedaj lahko oznaci samo enega na enkrat (bug pri request.params.get ...), popraviti to

    #TODO: ob kliku na gumb se tabela ne posodi sama od sebe, je potrebno osveziti stran, popraviti to
    #update: sedaj se stran osvezi ob kliku na gumb (samo potrebno je bilo sprementi parameter v location.reload()
    # na true. Ni sicer najlepsa resitev, lepse bi bilo, ce bi se tabele na strani posodobile, brez osvezitve strani.
    # Za to bi bilo potrebno bolj podrobno pogledati jquery.
def vrni_prvi_stolpec(seznam):
    #odstrani nepotrebne znake okrog besedila
    nov = []
    for i in seznam:
        nov.append(i[0])
    return nov

@get("/indexraziskovalec/")
def index_raziskovalec():
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    else:
        cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
        tmp1 = cur.fetchall()
        cur.execute("""SELECT DISTINCT ime FROM zdravilo
                    ORDER BY ime""")
        zdravilo_seznam = vrni_prvi_stolpec(cur.fetchall())
        cur.execute("""SELECT DISTINCT ime FROM bolezen
                    ORDER BY ime""")
        bolezen_seznam = vrni_prvi_stolpec(cur.fetchall())
        return template("indexraziskovalec.html", rows_spor = tmp1, user=curuser[0], zdravilo_seznam = zdravilo_seznam, bolezen_seznam = bolezen_seznam, click = 0)

def odstrani_nicle(seznam):
    """Odstrani nicle pri letu v seznamu tock, kjer so leta na prvem mestu v tocki"""
    nov_sez = []
    for element in seznam:
        nov_element = (int(element[0]), element[1])
        nov_sez.append(nov_element)
    return nov_sez
            
        

@post("/indexraziskovalec/")
def index_raziskovalec():
    curuser = get_user()
    if request.forms.zdravilo:
        cur.execute("""SELECT zdraviloid FROM zdravilo
                    WHERE ime = %s""",
                  [request.forms.zdravilo])
        zdravilo = cur.fetchone()[0]
        cur.execute("""SELECT leto, count(*) FROM 
                        (SELECT zdravilo, extract(year FROM datum) AS leto FROM pregled
                        JOIN diagnoza ON diagnoza = diagnozaid
                        WHERE zdravilo = %s) AS analiza
                        GROUP BY leto""", [zdravilo])
        rows_leto1 = cur.fetchall()
        cur.execute("""SELECT DISTINCT ime FROM zdravilo
                    ORDER BY ime""")
        zdravilo_seznam = vrni_prvi_stolpec(cur.fetchall())
        cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
        tmp1 = cur.fetchall()
        rows_leto = odstrani_nicle(rows_leto1)
        cur.execute("""SELECT DISTINCT ime FROM bolezen
                    ORDER BY ime""")
        bolezen_seznam = vrni_prvi_stolpec(cur.fetchall())
        return template("indexraziskovalec.html", rows_spor = tmp1, rows_leto = rows_leto, zdravilo_seznam = zdravilo_seznam, bolezen_seznam = bolezen_seznam, user=curuser[0], text = request.forms.zdravilo, click = 1)
    elif request.forms.bolezen:
        cur.execute("""SELECT bolezenid FROM bolezen
                    WHERE ime = %s""",
                  [request.forms.bolezen])
        bolezen = cur.fetchone()[0]
        cur.execute("""SELECT leto, count(*) FROM 
                        (SELECT bolezen, extract(year FROM datum) AS leto FROM pregled
                        JOIN diagnoza ON diagnoza = diagnozaid
                        WHERE bolezen= %s) AS analiza
                        GROUP BY leto""", [bolezen])
        rows_leto1 = cur.fetchall()
        cur.execute("""SELECT DISTINCT ime FROM zdravilo
                    ORDER BY ime""")
        zdravilo_seznam = vrni_prvi_stolpec(cur.fetchall())
        cur.execute("""SELECT DISTINCT ime FROM bolezen
                    ORDER BY ime""")
        bolezen_seznam = vrni_prvi_stolpec(cur.fetchall())
        cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
        tmp1 = cur.fetchall()
        rows_leto = odstrani_nicle(rows_leto1)
        return template("indexraziskovalec.html", rows_spor = tmp1, rows_leto = rows_leto, user=curuser[0], zdravilo_seznam = zdravilo_seznam, bolezen_seznam = bolezen_seznam, text = request.forms.bolezen, click = 1)                        


@get("/index/pregled/")
def pregled():
    curuser = get_user()
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC
                LIMIT 3""",
              [curuser[0]])
    tmp_spor = cur.fetchall()
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
                        zdravilo_seznam=zdravilo_seznam,
                        rows_spor = tmp_spor)

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

    c.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                    WHERE sporocila.prejemnik = %s
                    ORDER BY sporocila.datum DESC
                    LIMIT 3""",
                   [curuser[0]])
    tmp_spor = c.fetchall()

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

    izvid = request.forms.izvid
    if izvid == '':
        izvid = 'NULL'
    if request.forms.testNaprej != "":
        if request.forms.diagnoza != "" or request.forms.zdravilo != "":
            return template("pregled.html", user=curuser[0], napaka="Vnesete lahko ali samo šifro naslednjega testa ali samo diagnozo in zdravilo, ne oboje!",
                            test_seznam=test_seznam,
                            test_seznam2=test_seznam2, diagnoza_seznam=diagnoza_seznam,
                            zdravilo_seznam=zdravilo_seznam,
                            rows_spor=tmp_spor)
        c.execute("""SELECT testid FROM test
                    WHERE ime = %s""",
                  [request.forms.testNaprej])
        testNaprej = c.fetchone()[0]
        vrstica = [ID, zdravnik, testZdaj, testNaprej, izvid]
        c.execute("""INSERT INTO pregled (oseba,zdravnik,testZdaj,testNaprej,izvid)
                    VALUES (%s,%s,%s,%s,%s);""",vrstica)
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
                    VALUES (%s,%s,%s);""",vrstica2)
        c.execute("""SELECT diagnozaid FROM diagnoza
                    ORDER BY diagnozaid DESC
                    LIMIT 1;""")
        diagnozaid = c.fetchone()[0]
        vrstica1 = [ID, zdravnik, testZdaj, diagnozaid, izvid, diagnozaid, ID]
        c.execute("""INSERT INTO pregled (oseba,zdravnik,testZdaj,diagnoza,izvid)
                    VALUES (%s,%s,%s,%s,%s);
                    UPDATE pregled SET diagnoza = %s
                    WHERE oseba = %s AND diagnoza IS NULL""",vrstica1)
    redirect('/index/')



@get("/index/messenger/")
def messenger():
    '''Servira stran (na novi routi) z vsemi sporocili, tudi z vstavljanjem'''
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()
    return template("messenger.html", rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka=None)
    #return template("messenger.html", user=curuser[0])

@post("/index/messenger/")
def novo_sporocilo():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    prejID = request.forms.prejID
    sporocilo = request.forms.sporocilo
    curuser = get_user()
    cur.execute("SELECT * FROM uporabnik WHERE username=%s",
              [prejID])
    tmp_preveri = cur.fetchone()
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()

    if tmp_preveri is None:
        return template("messenger.html",
                               rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka="Ta prejemnik ne obstaja!")
    cur.execute("""INSERT INTO sporocila (posiljatelj, prejemnik, vsebina)
                VALUES (%s, %s, %s)""",
              [curuser[0], prejID, sporocilo])
    redirect('/index/messenger/')

@get("/indexraziskovalec/messenger/")
def messenger():
    '''Servira stran (na novi routi) z vsemi sporocili, tudi z vstavljanjem'''
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    elif pooblastilo(curuser[0]) == 'direktor':
        redirect('/indexdirektor/')
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()
    return template("messenger.html", rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka=None)
    #return template("messenger.html", user=curuser[0])

@post("/indexraziskovalec/messenger/")
def novo_sporocilo():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    prejID = request.forms.prejID
    sporocilo = request.forms.sporocilo
    curuser = get_user()
    cur.execute("SELECT * FROM uporabnik WHERE username=%s",
              [prejID])
    tmp_preveri = cur.fetchone()
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()

    if tmp_preveri is None:
        return template("messenger.html",
                               rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka="Ta prejemnik ne obstaja!")
    cur.execute("""INSERT INTO sporocila (posiljatelj, prejemnik, vsebina)
                VALUES (%s, %s, %s)""",
              [curuser[0], prejID, sporocilo])
    redirect('/index/messenger/')

@get("/indexdirektor/messenger/")
def messenger():
    '''Servira stran (na novi routi) z vsemi sporocili, tudi z vstavljanjem'''
    curuser = get_user()
    if pooblastilo(curuser[0]) == 'raziskovalec':
        redirect('/indexraziskovalec/')
    elif pooblastilo(curuser[0]) == 'zdravnik':
        redirect('/index/')
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()
    return template("messenger.html", rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka=None)
    #return template("messenger.html", user=curuser[0])

@post("/indexdirektor/messenger/")
def novo_sporocilo():
    ''' Vstavi novo sporocilo v tabelo sporocila.'''
    prejID = request.forms.prejID
    sporocilo = request.forms.sporocilo
    curuser = get_user()
    cur.execute("SELECT * FROM uporabnik WHERE username=%s",
              [prejID])
    tmp_preveri = cur.fetchone()
    cur.execute("""SELECT posiljatelj, datum, vsebina FROM sporocila
                WHERE sporocila.prejemnik = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp = cur.fetchall()
    cur.execute("""SELECT prejemnik, datum, vsebina FROM sporocila
                WHERE sporocila.posiljatelj = %s
                ORDER BY sporocila.datum DESC""",
              [curuser[0]])
    tmp1 = cur.fetchall()

    if tmp_preveri is None:
        return template("messenger.html",
                               rows=tmp, rows_p = tmp1, user=curuser[0], prejID=None, napaka="Ta prejemnik ne obstaja!")
    cur.execute("""INSERT INTO sporocila (posiljatelj, prejemnik, vsebina)
                VALUES (%s, %s, %s)""",
              [curuser[0], prejID, sporocilo])
    redirect('/index/messenger/')


run(host='localhost', port=8080)



