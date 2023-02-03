import database
import hashlib
import models
import flask
import os

app = flask.Flask(__name__)
if not os.path.exists(".docker"):
    print("Not in docker... Using external database server...")
    import dotenv
    dotenv.load_dotenv(dotenv_path = os.path.join("..", "db.env"))
    db_host = "192.168.1.5"
else:
    db_host = "db"

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

@app.route("/api/signin", methods = ["POST"])
def signin():
    """Signin api endpoint. POST request at ``/api/signin``, must be a
    JSON object with exactly the keys ``'pass', 'sname', 'fname', 'email'``.

    Example curl request:

    .. code-block:: bash

        curl -X POST -F 'email=gae19jtu@uea.ac.uk' -F 'fname=Eden' -F 'sname=Attenborough' -F 'pass=password' http://127.0.0.1:2004/api/signin

    """
    req = dict(flask.request.form)
    if set(req.keys()) != {'pass', 'sname', 'fname', 'email'}:
        return flask.abort(400)

    with database.MowerDatabase(host = db_host) as db:
        try:
            session_id, expires_at = db.authenticate_user(req["email"], hash_pw(req["pass"]))
        except database.UnauthenticatedUserException as e:
            return flask.abort(401)

    resp = flask.make_response(flask.jsonify({"poggers": "authentication successful"}))
    resp.set_cookie("session", value = session_id, expires = expires_at)

    return resp

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 2004, debug = True)

# if __name__ == "__main__":

#     with database.MowerDatabase(host = host) as db:
#         db.create_user("gae19jtu@uea.ac.uk", "Eden", "Attenborough", hash_pw("password"))

#         session_id, expires_at = db.authenticate_user("gae19jtu@uea.ac.uk", hash_pw("password"))
#         print(db.authenticate_session(session_id))

#         # print(db.authenticate_session("a"))

#         area = models.Area(db.authenticate_session(session_id), "UEA 1", "By the big tree", [(1.1, 2.2, 3.3), (1.2, 2.4, 6.6)], [[(3.0, 4.0, 6.0)]])
#         # area2 = models.Area(db.authenticate_session(session_id), "UEA 2", "Left of the car park", [(1.0, 2.0, 3.0)], None)
        
#         print(db.create_area(area))
