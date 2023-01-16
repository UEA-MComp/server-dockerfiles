import database
import hashlib

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

if __name__ == "__main__":
    with database.MowerDatabase() as db:
        db.create_user("gae19jtu@uea.ac.uk", "Eden", "Attenborough", hash_pw("password"))

        print(db.authenticate_user("gae19jtu@uea.ac.uk", hash_pw("password")))