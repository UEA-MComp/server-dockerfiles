from dataclasses import dataclass
import pymysql
import os

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
    passwd: str = os.environ["MYSQL_ROOT_PASSWORD"]
    db: str = "mower"
    port: int = 3306

    def __enter__(self):
        try:
            self.__connection = self.__get_connection()
        except Exception as e:
            print(e.args[1])
            if e.args[0] == 1049:
                self.__build_db()
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
                sname VARCHAR(50) NOT NULL
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
                x_whole INT NOT NULL,
                x_decimal BIGINT UNSIGNED NOT NULL,
                y_whole INT NOT NULL,
                y_decimal BIGINT UNSIGNED NOT NULL,
                z_whole INT NOT NULL,
                z_decimal BIGINT UNSIGNED NOT NULL
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
                FORIEGN KEY (coord_id) REFERENCES coords (coord_id),
                FOREIGN KEY (area_id) REFERENCES mower_areas (area_id),
                PRIMARY KEY (coord_id, area_id)
            );
            """)
            cursor.execute("""
            CREATE TABLE nogo_coords (
                coord_id INT UNSIGNED NOT NULL,
                nogo_id INT UNSIGNED NOT NULL,
                PRIMARY KEY (coord_id, nogo_id),
                FORIEGN KEY (coord_id) REFERENCES coords (coord_id),
                FOREIGN KEY (nogo_id) REFERENCES nogo_zones (nogo_id)
            );
            """)

            self.__connection.commit()
            return self.__connection
