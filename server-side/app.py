import database
import hashlib
import os

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = os.path.join("..", "db.env"))
        host = "127.0.0.1"
    else:
        host = "db"

    with database.MowerDatabase(host = host) as db:
        db.create_user("gae19jtu@uea.ac.uk", "Eden", "Attenborough", hash_pw("password"))

        print(db.authenticate_user("gae19jtu@uea.ac.uk", hash_pw("password")))
