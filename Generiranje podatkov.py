#podatki

import pandas as pd
test = pd.read_csv('C:\\Faks\\OPB\\e-kartoteka\\podatki\\test.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['testiD', 'imena'],
                   sep = ';')
testID = list(test.testiD)

bolezen = pd.read_csv('C:\\Faks\\OPB\\e-kartoteka\\podatki\\bolezen.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['bolezenID', 'imena'],
                   sep = ';')
bolezenID = list(bolezen.bolezenID)

zdravilo = pd.read_csv('C:\\Faks\\OPB\\e-kartoteka\\podatki\\zdravilo.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   header=None,
                   names=['zdraviloID', 'imena'],
                   sep = ';')
zdraviloID = list(zdravilo.zdraviloID)

datumi = pd.read_csv('C:\\Faks\\OPB\\e-kartoteka\\podatki\\datumi.csv', encoding = "ISO-8859-1",
                   error_bad_lines=False,
                   sep = ';')
datum = list(datumi.datum)

import random


def naredi_podatke_specializacija(stevilo, datoteka):
    #generira INSERT SQL stavke za tabelo specializacija in jih zapise v datoteko
    zdravniki = [i + 1 for i in range(200)]
    with open(datoteka, "w") as text_file:
        for j in range(stevilo):
            vrstica = [random.choice(zdravniki), random.choice(testID)]
            text_file.write("INSERT INTO specializacija(zdravnik,test) VALUES ({0},'{1}');".format(*vrstica))


specializacija = 'C:\\Faks\\OPB\\e-kartoteka\\podatki\\specializacija.txt'

#naredi_podatke_specializacija(500, specializacija)

def naredi_podatke_diagnoza(stevilo, datoteka):
    # generira INSERT SQL stavke za tabelo diagnoza in jih zapise v datoteko
    zdravniki = [i + 1 for i in range(200)]
    with open(datoteka, "w") as text_file:
        for j in range(stevilo):
            vrstica = [random.choice(bolezenID), random.choice(zdraviloID), random.choice(zdravniki)]
            text_file.write("INSERT INTO diagnoza(bolezen,zdravilo,zdravnik) VALUES ('{0}',{1}, {2});".format(*vrstica))


diagnoza = 'C:\\Faks\\OPB\\e-kartoteka\\podatki\\diagnoza.txt'

#naredi_podatke_diagnoza(10000, diagnoza)

import time

def strTimeProp(start, end, format, prop):
    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))
    ptime = stime + prop * (etime - stime)
    return time.strftime(format, time.localtime(ptime))

def randomDate(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%d', prop)

randomDate("2018-1-1", "2018-2-2", random.random())

def naredi_podatke_pregled(datoteka):
    # generira INSERT SQL stavke za tabelo pregled in jih zapise v datoteko
    zdravniki = [i + 1 for i in range(200)]
    osebe = [i + 2 for i in range(1000)]
    st_pregledov = [1,2,3,4,5,6]
    with open(datoteka, "w") as text_file:
        for j in range(10000): #enako številu diagnoz
            i = random.choice(st_pregledov)
            testNaprej = random.choice(testID)
            date = random.choice(datum)
            for k in range(i):
                testZdaj = testNaprej
                testNaprej = random.choice(testID)
                vrstica = [random.choice(osebe), random.choice(zdravniki), testZdaj, testNaprej, j+1, 'NULL', date]
                if k == i-1:
                    text_file.write(
                        "INSERT INTO pregled(oseba,zdravnik, testZdaj,testNaprej, diagnoza, izvid, datum) VALUES "
                        "({0},{1},'{2}',NULL,{4},{5},'{6}');".format(*vrstica))
                text_file.write("INSERT INTO pregled(oseba,zdravnik, testZdaj,testNaprej, diagnoza, izvid, datum) VALUES "
                                "({0},{1},'{2}','{3}',{4},{5},'{6}');".format(*vrstica))
                date = randomDate(date, "2018-5-5", random.random())

pregled = 'C:\\Faks\\OPB\\e-kartoteka\\podatki\\pregled.txt'

naredi_podatke_pregled(pregled)