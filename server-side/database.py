from dataclasses import dataclass
import datetime
import pymysql
import secrets
import models
import os

SESSION_LENGTH = datetime.timedelta(days = 7)

@dataclass
class MowerDatabase:
    """Class for interfacing with the MariaDB database. Default
    configs are appropriate for the docker config. Expected to be used with a ``with``
    block. Database will be built if it doesn't exist.

    Returns:
        MowerDatabase: database object
    """
    host: str = "db"
    user: str = "root"
    passwd: str = None
    db: str = "mower"
    port: int = 3306

    def __enter__(self):
        if self.passwd is None:
            self.passwd = os.environ["MYSQL_ROOT_PASSWORD"]
            
        try:
            self.__connection = self.__get_connection()
        except Exception as e:
            print(e)
            if e.args[0] == 1049:
                self.__connection = self.__build_db()
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def __get_connection(self):
        return pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
            database = self.db
        )

    def __build_db(self):
        print("Building database...")
        self.__connection = pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
        )
        with self.__connection.cursor() as cursor:
            # unsafe:
            cursor.execute("CREATE DATABASE %s" % self.db)
            cursor.execute("USE %s" % self.db)

            cursor.execute("""
            CREATE TABLE users (
                user_no INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(50) NOT NULL,
                fname VARCHAR(50) NOT NULL,
                sname VARCHAR(50) NOT NULL,
                pw_hash CHAR(64) NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE sessions (
                cookie_bytes CHAR(32) PRIMARY KEY,
                user_no INT UNSIGNED NOT NULL,
                created_at DATETIME NOT NULL DEFAULT NOW(),
                expire_at DATETIME NOT NULL,
                client_info TEXT,
                FOREIGN KEY (user_no) REFERENCES users (user_no)
            );
            """)
            # use two separate points for whole and decimal parts
            # because im not sure about mysql's floating point
            # precision... we need a lot of accuracy here
            cursor.execute("""
            CREATE TABLE coords (
                coord_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                x VARCHAR(20) NOT NULL,
                y VARCHAR(20) NOT NULL,
                z VARCHAR(20) NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE mower_areas (
                area_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                user_no INT UNSIGNED NOT NULL,
                area_name VARCHAR(100) NOT NULL,
                area_notes TEXT NULL,
                FOREIGN KEY (user_no) REFERENCES users (user_no)
            );
            """)
            cursor.execute("""
            CREATE TABLE nogo_zones (
                nogo_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                area_id INT UNSIGNED NOT NULL,
                FOREIGN KEY (area_id) REFERENCES mower_areas (area_id)
            );
            """)
            cursor.execute("""
            CREATE TABLE area_coords (
                coord_id INT UNSIGNED NOT NULL,
                area_id INT UNSIGNED NOT NULL,
                PRIMARY KEY (coord_id, area_id)
            );
            """)
            cursor.execute("ALTER TABLE area_coords ADD FOREIGN KEY (area_id) REFERENCES mower_areas (area_id);")
            cursor.execute("ALTER TABLE area_coords ADD FOREIGN KEY (coord_id) REFERENCES coords (coord_id);")
            cursor.execute("""
            CREATE TABLE nogo_coords (
                coord_id INT UNSIGNED NOT NULL,
                nogo_id INT UNSIGNED NOT NULL,
                PRIMARY KEY (coord_id, nogo_id),
                FOREIGN KEY (coord_id) REFERENCES coords (coord_id),
                FOREIGN KEY (nogo_id) REFERENCES nogo_zones (nogo_id)
            );
            """)
            cursor.execute("""
            CREATE TABLE mowers (
                iqn VARCHAR(50) PRIMARY KEY NOT NULL,
                vpn_ip CHAR(11) NOT NULL,
                owner INT UNSIGNED NOT NULL,
                FOREIGN KEY (owner) REFERENCES users (user_no)
            );
            """)
            cursor.execute("""
            CREATE TABLE nmea_logs (
                mower VARCHAR(50) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT NOW(),
                last_updated DATETIME NOT NULL DEFAULT NOW(),
                path VARCHAR(100) NOT NULL,
                FOREIGN KEY (mower) REFERENCES mowers(iqn),
                PRIMARY KEY(mower, created_at)
            );
            """)
            cursor.execute("""
            CREATE TABLE telemetry (
                mower VARCHAR(50) NOT NULL,
                recv_at DATETIME NOT NULL,
                coord INT UNSIGNED NOT NULL,
                FOREIGN KEY (mower) REFERENCES mowers(iqn),
                FOREIGN KEY (coord) REFERENCES coords(coord_id),
                PRIMARY KEY (mower, recv_at)
            );
            """)

            self.__connection.commit()
            return self.__connection

    def create_user(self, email, fname, sname, pw_hashed):
        """Appends a user to the database, then returns a new session id for this user.

        Todo: 
            * Throw some sort of exception if the email already exists

        Arguments:
            email (str): The user's email
            fname (str): The user's first name
            sname (str): The user's surname
            pw_hashed (str): The user's password, already hashed as SHA256

        Returns:
            (str, datetime.datetime): A session id for this new user, with an expiration datetime (see :meth:`database.MowerDatabase.authenticate_user`)
        """
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO users (email, fname, sname, pw_hash)
            VALUES (%s, %s, %s, %s);
            """, (email, fname, sname, pw_hashed, ))
        self.__connection.commit()

        return self.authenticate_user(email, pw_hashed)

    def authenticate_user(self, email, pw_hashed, client_info = 'API Client'):
        """Returns a new session id for a given username and password.

        Arguments:
            email (str): The user's email
            pw_hashed (str): A user's password associated with that email, hashed as SHA256

        Raises:
            UnauthenticatedUserException: If the username isn't found or the password is wrong

        Returns:
            (str, datetime): A tuple consisting of a session id, and its associated expiry datetime
        """
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT user_no FROM users WHERE email = %s AND pw_hash = %s;
            """, (email, pw_hashed, ))
            try:
                user_id = int(cursor.fetchone()[0])
            except:
                raise UnauthenticatedUserException("User not found, or incorrect password")

            session_id = secrets.token_hex(16)
            expiration_dt = datetime.datetime.now() + SESSION_LENGTH
            # print(session_id, expiration_dt)
            cursor.execute("INSERT INTO sessions (cookie_bytes, user_no, expire_at, client_info) VALUES (%s, %s, %s, %s);",
                (session_id, user_id, expiration_dt, client_info), 
            )

        self.__connection.commit()
        return session_id, expiration_dt

    def authenticate_session(self, session_id):
        """Returns the associated :class:`models.User` for an associated session id.

        Arguments:
            session_id (str): A session id cookie

        Raises:
            InvalidSessionException: If the session isn't found in the database, for example if it has expired

        Returns:
            models.User: An associated user model
        """
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT users.user_no, email, fname, sname FROM users WHERE user_no = (
                SELECT user_no FROM sessions WHERE cookie_bytes = %s
            );""", (session_id, ))
            try:
                id_, email, fname, sname = cursor.fetchone()
            except:
                raise InvalidSessionException("The session id '%s' was not found in the database." % session_id)

        return models.User(id_, email, fname, sname)

    def create_area(self, area: models.Area):
        """Append a given :class:`models.Area` to the database. A valid :class:`models.User` 
        must be set in the area object

        Arguments:
            area (models.Area): An area to add
        """
        with self.__connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mower_areas (user_no, area_name, area_notes) VALUES (%s, %s, %s)", 
                (area.owner.id_, area.name, area.notes)
            )
            area_id = cursor.lastrowid

            for x, y, z in area.area_coords:
                cursor.execute(
                    """
                    INSERT INTO coords (x, y, z)
                    VALUES (%s, %s, %s)
                    """,
                    (str(x), str(y), str(z))
                )
                coord_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO area_coords VALUES (%s, %s);",
                    (coord_id, area_id)
                )

            for nogo_zone in area.nogo_zones:

                cursor.execute(
                    "INSERT INTO nogo_zones (area_id) VALUES (%s);",
                    (area_id, )
                )
                nogo_id = cursor.lastrowid

                for x, y, z in nogo_zone:
                    cursor.execute(
                        """
                        INSERT INTO coords (x, y, z)
                        VALUES (%s, %s, %s)
                        """,
                        (str(x), str(y), str(z))
                    )
                    coord_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO nogo_coords VALUES (%s, %s);",
                        (coord_id, nogo_id)
                    )


        self.__connection.commit()

    def get_areas(self, user: models.User):
        """Returns a list of all the :class:`models.Area` s associated with a given :class:`models.User`.

        Arguments:
            user (models.User): A user to get the :class:`models.Area` s for
        """
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT area_id, area_name, area_notes FROM mower_areas WHERE user_no = %s;", (user.id_, ))

            areas = []
            for area_id, area_name, area_notes in cursor.fetchall():
                cursor.execute("""
                SELECT x, y, z FROM area_coords 
                INNER JOIN coords ON coords.coord_id = area_coords.coord_id 
                WHERE area_coords.area_id = %s;
                """, (area_id, ))
                coords = str_coords_to_float(cursor.fetchall())

                nogo_zones = []
                cursor.execute("SELECT nogo_id FROM nogo_zones WHERE area_id = %s;", (area_id, ))
                for nogo_id in [i[0] for i in cursor.fetchall()]:
                    cursor.execute("""
                    SELECT x, y, z FROM nogo_coords 
                    INNER JOIN coords ON nogo_coords.coord_id = coords.coord_id 
                    WHERE nogo_id = %s;
                    """, (nogo_id, ))
                    nogo_zones.append(str_coords_to_float(cursor.fetchall()))

                areas.append(models.Area(user, area_name, area_notes, coords, nogo_zones))

                # print(area_id, area_name, area_notes)
                # print(coords)
                # print(nogo_zones)

                # break
        
        return areas

    def append_mowers(self, user: models.User, iqn: str, vpn_ip: str):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO mowers VALUES (%s, %s, %s);", (iqn, vpn_ip, user.id_))
        self.__connection.commit()

    def get_nmea_logfile(self, iqn: str, basedir: str, max_age: int = 60):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT path FROM nmea_logs WHERE TIMESTAMPDIFF(SECOND, last_updated, NOW()) <= %s;", (max_age, ))
            o = cursor.fetchone()
            if o is not None:
                return o[0]

            now = datetime.datetime.now()
            nmea_path = os.path.join(basedir, "%s_%s.nmea" % (iqn, now.isoformat()))
            cursor.execute("INSERT INTO nmea_logs (mower, created_at, path) VALUES (%s, %s, %s);", (iqn, now, nmea_path))
        self.__connection.commit()
        return nmea_path

    def append_nmea_logfile(self, sentence, iqn: str, basedir: str, max_age: int = 60):
        path = self.get_nmea_logfile(iqn, basedir, max_age)
        with open(path, "ab") as f:
            f.write(sentence)

        with self.__connection.cursor() as cursor:
            cursor.execute("UPDATE nmea_logs SET last_updated = NOW() WHERE path = %s;", (path, ))
        self.__connection.commit()

    def append_telemetry(self, iqn: str, timestamp, x, y, z):
        with self.__connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO coords (x, y, z)
                VALUES (%s, %s, %s)
                """,
                (str(x), str(y), str(z))
            )
            coord_id = cursor.lastrowid

            cursor.execute("INSERT INTO telemetry VALUES (%s, %s, %s);", (iqn, timestamp, coord_id))
        self.__connection.commit()

def str_coords_to_float(coords):
    return [[float(j) for j in i] for i in coords]

class UnauthenticatedUserException(Exception):
    pass

class InvalidSessionException(Exception):
    pass

if __name__ == "__main__":
    import app
    with MowerDatabase(host = "192.168.1.9") as db:
        # print(db.create_user("gae19jtu@uea.ac.uk", "Eden", "Attenborough", app.hash_pw("passwd")))
        session_id = "c3c4ebdcb7d05cae92aaa465054f1c4d"
        db.append_mowers(db.authenticate_session(session_id), "iqn.2004-10.com.ubuntu:01:bb98777ca2f4", "10.13.13.2")
        # for i in range(100):
        #     sentence = b"hewwo worrd uwuwu %d\r\n" % i
        #     db.append_nmea_logfile(sentence,"iqn.2004-10.com.ubuntu:01:bb98777ca2f4", "/home/pi/logs")
        #db.append_telemetry("iqn.2004-10.com.ubuntu:01:bb98777ca2f4", datetime.datetime.now(), 52.6295245717, -19.703, 1.2696029833)
