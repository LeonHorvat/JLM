#podatki

import pandas as pd
test = pd.read_csv('podatki/test.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['testiD', 'imena'],
                   sep = ';')
testID = list(test.testiD)

bolezen = pd.read_csv('podatki/bolezen.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['bolezenID', 'imena'],
                   sep = ';')
bolezenID = list(bolezen.bolezenID)

zdravilo = pd.read_csv('podatki/zdravilo.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['zdraviloID', 'imena'],
                   sep = ';')
zdraviloID = list(zdravilo.zdraviloID)

datumi = pd.read_csv('podatki/datumi.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   sep = ';')
datum = list(datumi.datum)

uporabniki = pd.read_csv('podatki/uporabniki.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   sep = ',')
geslo = list(uporabniki.password)
username = list(uporabniki.username)
pooblastilo = list(uporabniki.pooblastilo)

zdravniki = pd.read_csv('podatki/zdravniki.csv', encoding = 'utf8',
                   error_bad_lines=False,
                   sep = ',')
ime = list(zdravniki.ime)
priimek = list(zdravniki.priimek)
rojstvo = list(zdravniki.rojstvo)

osebe = pd.read_csv('podatki/oseba.csv', encoding = 'utf8',
                   error_bad_lines=False,
                   sep = ',')


import random

def username_zdravnik(username, pooblastilo):
    zdravnik_user = []
    for j in range(len(username)):
        if pooblastilo[j] == 'zdravnik':
            zdravnik_user.append(username[j])
    return zdravnik_user

def naredi_podatke_specializacija(stevilo, datoteka, username, pooblastilo):
    #generira INSERT SQL stavke za tabelo specializacija in jih zapise v datoteko
    zdravniki = username_zdravnik(username, pooblastilo)
    with open(datoteka, "w") as text_file:
        for j in range(stevilo):
            vrstica = [random.choice(zdravniki), random.choice(testID)]
            text_file.write("INSERT INTO specializacija(zdravnik,test) VALUES ('{0}','{1}');".format(*vrstica))


specializacija = 'podatki/specializacija.txt'

#naredi_podatke_specializacija(500, specializacija, username, pooblastilo)

def naredi_podatke_diagnoza(stevilo, datoteka, username, pooblastilo):
    # generira INSERT SQL stavke za tabelo diagnoza in jih zapise v datoteko
    zdravniki = username_zdravnik(username, pooblastilo)
    with open(datoteka, "w") as text_file:
        for j in range(stevilo):
            vrstica = [random.choice(bolezenID), random.choice(zdraviloID), random.choice(zdravniki)]
            text_file.write("INSERT INTO diagnoza(bolezen,zdravilo,zdravnik) VALUES ('{0}',{1}, '{2}');".format(*vrstica))


diagnoza = 'podatki/diagnoza.txt'

#naredi_podatke_diagnoza(10000, diagnoza, username, pooblastilo)

import time

def strTimeProp(start, end, format, prop):
    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))
    ptime = stime + prop * (etime - stime)
    return time.strftime(format, time.localtime(ptime))

def randomDate(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%d', prop)

randomDate("2018-1-1", "2018-2-2", random.random())

def naredi_podatke_pregled(datoteka, username, pooblastilo):
    # generira INSERT SQL stavke za tabelo pregled in jih zapise v datoteko
    zdravniki = username_zdravnik(username, pooblastilo)
    osebe = [i + 1 for i in range(1000)]
    st_pregledov = [1,2,3,4,5,6]
    with open(datoteka, "w") as text_file:
        for j in range(10000): #enako številu diagnoz
            i = random.choice(st_pregledov)
            testNaprej = random.choice(testID)
            date = random.choice(datum)
            oseba = random.choice(osebe)
            for k in range(i):
                testZdaj = testNaprej
                testNaprej = random.choice(testID)
                vrstica = [oseba, random.choice(zdravniki), testZdaj, testNaprej, j+1, 'NULL', date]
                if k == i-1:
                    text_file.write(
                        "INSERT INTO pregled(oseba,zdravnik, testZdaj,testNaprej, diagnoza, izvid, datum) VALUES "
                        "({0},'{1}','{2}',NULL,{4},{5},'{6}');".format(*vrstica))
                else:
                    text_file.write("INSERT INTO pregled(oseba,zdravnik, testZdaj,testNaprej, diagnoza, izvid, datum) VALUES "
                                    "({0},'{1}','{2}','{3}',{4},{5},'{6}');".format(*vrstica))
                date = randomDate(date, "2018-5-5", random.random())

pregled = 'podatki/pregled.txt'

naredi_podatke_pregled(pregled, username, pooblastilo)


import hashlib

def naredi_hash(geslo):
    #Naredi hash podanega gesla
    h = hashlib.md5()
    h.update(geslo.encode('utf-8'))
    return h.hexdigest()

def pretvori_gesla_v_hash(geslo):
    #pretvori seznam gesel v seznam hash-ov
    h = []
    for i in geslo:
        a = naredi_hash(i)
        h.append(a)
    return h

def naredi_podatke_uporabniki(uporabnik, geslo, pooblastilo, datoteka):
    hash = pretvori_gesla_v_hash(geslo)
    with open(datoteka, "w") as text_file:
        for j in range(len(uporabnik)):
            vrstica = [uporabnik[j], hash[j], pooblastilo[j]]
            text_file.write("INSERT INTO uporabnik(username,hash,pooblastilo) VALUES ('{0}','{1}','{2}');".format(*vrstica))

uporabnik = 'podatki/uporabnik.txt'

#naredi_podatke_uporabniki(username, geslo, pooblastilo, uporabnik)

# tabela z gesli in hashi - zasebna
hash = pretvori_gesla_v_hash(geslo)
hash = pd.DataFrame({'hash': hash})
uporabniki_zasebno = uporabniki.join(hash)
#uporabniki_zasebno.to_csv(path_or_buf='C:/Faks/OPB/uporabniki_zasebno.csv', sep=';', na_rep='', float_format=None, columns=None, header=True, index=False, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='\n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal=',')


def naredi_podatke_zdravnik(uporabnik, ime, priimek, rojstvo, pooblastilo, datoteka):
    with open(datoteka, "w") as text_file:
        for j in range(len(uporabnik)):
            if pooblastilo[j] == 'zdravnik':
                vrstica = [uporabnik[j], ime[j], priimek[j], rojstvo[j]]
                text_file.write("INSERT INTO zdravnik(zdravnikID,ime,priimek,rojstvo) VALUES ('{0}','{1}','{2}','{3}');".format(*vrstica))

zdravnik = 'podatki/zdravnik.txt'

#naredi_podatke_zdravnik(username, ime, priimek, rojstvo, pooblastilo, zdravnik)

def naredi_podatke_oseba(osebe, zdravniki, datoteka):
    ime = list(osebe.ime)
    priimek = list(osebe.priimek)
    rojstvo = list(osebe.rojstvo)
    naslov = list(osebe.naslov)
    kri = list(osebe.kri)
    teza = list(osebe.teza)
    visina = list(osebe.visina)
    with open(datoteka, "w") as text_file:
        for j in range(len(ime)):
            osebniZdravnik = random.choice(zdravniki)
            vrstica = [ime[j], priimek[j], rojstvo[j], naslov[j], kri[j], teza[j], visina[j], osebniZdravnik]
            text_file.write("INSERT INTO oseba(ime,priimek,rojstvo,naslov,kri,teza,visina,osebniZdravnik) VALUES ('{0}','{1}','{2}','{3}','{4}',{5},{6},'{7}');".format(*vrstica))

oseba = 'podatki/oseba.txt'

#naredi_podatke_oseba(osebe, username_zdravnik(username, pooblastilo), oseba)
