DROP TABLE IF EXISTS zdravnik CASCADE;
DROP TABLE IF EXISTS oseba CASCADE;
DROP TABLE IF EXISTS pregled CASCADE;
DROP TABLE IF EXISTS test CASCADE;
DROP TABLE IF EXISTS specializacija CASCADE;
DROP TABLE IF EXISTS diagnoza CASCADE;
DROP TABLE IF EXISTS bolezen CASCADE;
DROP TABLE IF EXISTS zdravilo CASCADE;

CREATE TABLE bolezen (
	bolezenID TEXT PRIMARY KEY,
	ime TEXT NOT NULL
);

CREATE TABLE zdravilo (
	zdraviloID INTEGER PRIMARY KEY,
	ime TEXT UNIQUE NOT NULL
);

CREATE TABLE test (
	testID TEXT PRIMARY KEY,
	ime TEXT NOT NULL /* TEXT oblike zaradi prilagoditve indeksem srovih podatkov*/
);

CREATE TABLE zdravnik (
	zdravnikID TEXT PRIMARY KEY,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL
);

CREATE TABLE oseba (
	osebaID SERIAL PRIMARY KEY,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL,
	naslov TEXT NOT NULL,
	kri TEXT NOT NULL,
	teza DECIMAL NOT NULL,
	visina DECIMAL NOT NULL,
	osebniZdravnik TEXT NOT NULL REFERENCES zdravnik(zdravnikID),
	CONSTRAINT sam_svoj_zdravnik CHECK (/* TODO*/),
	CONSTRAINT napoved_rojstva CHECK (rojstvo <= now()),
	CONSTRAINT nepozitivna_teza CHECK (teza > 0),
	CONSTRAINT nepozitivna_visina CHECK (visina > 0)
);

CREATE TABLE specializacija (
    zdravnik TEXT NOT NULL REFERENCES zdravnik(zdravnikID) ON DELETE CASCADE,
    test TEXT NOT NULL REFERENCES test(testID) ON DELETE CASCADE,
    PRIMARY KEY (zdravnik, test)
);

CREATE TABLE diagnoza (
	diagnozaID SERIAL PRIMARY KEY,
	bolezen TEXT NOT NULL REFERENCES bolezen(bolezenID),
	zdravilo INTEGER NOT NULL REFERENCES zdravilo(zdraviloID),
	zdravnik TEXT NOT NULL REFERENCES zdravnik(zdravnikID)
);

CREATE TABLE pregled (
    pregledID SERIAL PRIMARY KEY,
	oseba INTEGER NOT NULL REFERENCES oseba(osebaID),
	zdravnik TEXT NOT NULL REFERENCES zdravnik(zdravnikID),
	testZdaj TEXT NOT NULL REFERENCES test(testID),
	testNaprej TEXT REFERENCES test(testID) DEFAULT NULL,
	diagnoza INTEGER REFERENCES diagnoza(diagnozaID) DEFAULT NULL,
	izvid TEXT,
	datum DATE DEFAULT now(), 
	CONSTRAINT napoved_pregleda CHECK (datum <= now()),
	CONSTRAINT brez_diagnoze_in_napotnice CHECK (testNaprej IS NOT NULL OR diagnoza IS NOT NULL)
);

CREATE TABLE uporabnik (
	username TEXT PRIMARY KEY,
	hash TEXT NOT NULL,
	pooblastilo TEXT NOT NULL
);




GRANT ALL ON ALL TABLES IN SCHEMA public TO metodj;
GRANT ALL ON ALL TABLES IN SCHEMA public TO leonh;
GRANT ALL ON ALL TABLES IN SCHEMA public TO jernejb;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO metodj;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO leonh;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO jernejb;


/* preveri če deluje - vprašljiva funkcionalnost*/
DROP TRIGGER IF EXISTS posodobitev ON pregled CASCADE;
DROP FUNCTION IF EXISTS posodobitev();

CREATE FUNCTION posodobitev() RETURNS trigger AS $posodobitev$
    BEGIN
        IF (NEW.diagnoza <> NULL) THEN
			UPDATE pregled SET diagnoza = NEW.diagnoza 
			WHERE pregled(oseba) = NEW.oseba AND pregled(diagnoza) = NULL;
		END IF;
    END;
$posodobitev$ LANGUAGE plpgsql;

CREATE TRIGGER posodobitev AFTER INSERT ON pregled
    FOR EACH ROW EXECUTE PROCEDURE posodobitev();

/* ============ KOPIRAJ LE DO TU, KODA SPODAJ ŠE NE DELUJE ============ */


/* Definiral zgolj za nadaljevanje za določene pravice, ki komu pripadajo - role "zdravnik" tu še ne obstaja*/ 
GRANT SELECT, UPDATE, INSERT ON pregled IN SCHEMA public TO zdravnik_uporabnik;
GRANT SELECT, UPDATE, INSERT ON zdravnik IN SCHEMA public TO direktor_uporabnik;
GRANT SELECT, UPDATE, INSERT ON zdravilo IN SCHEMA public TO direktor_uporabnik;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO zdravnik_uporabnik;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO pacient_uporabnik;

