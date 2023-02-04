from paste.translogger import TransLogger
import database
import waitress
import hashlib
import models
import flask
import sys
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

def authenticate():
    if flask.request.cookies.get("session") is None:
        return flask.abort(401)
    with database.MowerDatabase(host = db_host) as db:
        try:
            return db.authenticate_session(flask.request.cookies.get("session"))
        except database.InvalidSessionException as e:
            return flask.abort(401)

@app.route("/api/signin", methods = ["POST"])
def signin():
    """
    +----------+------------------+
    |          | API Endpoint     |
    +==========+==================+
    | Endpoint | ``/api/signin``  |
    +----------+------------------+
    | Method   | POST             |
    +----------+------------------+
    | Cookie   | **No**           |
    +----------+------------------+
    
    Signin api endpoint. POST request at ``/api/signin``, must be a
    JSON object with exactly the keys ``'pass', 'sname', 'fname', 'email'``.
    Returns a session cookie which can be used for subsequent requests.
    The password is unhashed at this stage.

    Example curl request:

    .. code-block:: bash

        curl -H "Content-Type: application/json" --request POST --data '{"email":"gae19jtu@uea.ac.uk", "sname":"Attenborough", "pass":"password", "fname":"Eden"}' http://127.0.0.1:2004/api/signin

    Example valid result content:

    .. code-block:: json

        {
            "success": "authentication successful"
        }

    """
    req = flask.request.json
    # print(req)
    if set(req.keys()) != {'pass', 'sname', 'fname', 'email'}:
        return flask.abort(400, "The JSON keys {'pass', 'sname', 'fname', 'email'} are required")

    with database.MowerDatabase(host = db_host) as db:
        try:
            session_id, expires_at = db.authenticate_user(req["email"], hash_pw(req["pass"]))
        except database.UnauthenticatedUserException as e:
            return flask.abort(401)

    resp = flask.make_response(flask.jsonify({"success": "authentication successful"}))
    resp.set_cookie("session", value = session_id, expires = expires_at)

    return resp

@app.route("/api/adduser", methods = ["POST"])
def adduser():
    """
    +----------+------------------+
    |          | API Endpoint     |
    +==========+==================+
    | Endpoint | ``/api/adduser`` |
    +----------+------------------+
    | Method   | POST             |
    +----------+------------------+
    | Cookie   | **No**           |
    +----------+------------------+

    Very similar to :func:`signin`, except this creates a new account.
    Returns a valid session cookie for subsequent requests.

    Example curl request:

    .. code-block:: bash

        curl -v -H "Content-Type: application/json" --request POST --data '{"email":"gae19jtu@uea.ac.uk", "sname":"Attenborough", "pass":"password", "fname":"EdenTwo"}' http://127.0.0.1:2004/api/adduser

    Example JSON response:

    .. code-block:: json

        {
            "success": "a new user was created and the session cookie returned"
        }

    """

    req = flask.request.json
    # print(req)
    if set(req.keys()) != {'pass', 'sname', 'fname', 'email'}:
        return flask.abort(400, "The JSON keys {'pass', 'sname', 'fname', 'email'} are required")

    with database.MowerDatabase(host = db_host) as db:
        session_id, expires_at = db.create_user(req["email"], req["fname"], req["sname"], hash_pw(req["pass"]))

    resp = flask.make_response(flask.jsonify({"success": "a new user was created and the session cookie returned"}))
    resp.set_cookie("session", value = session_id, expires = expires_at)

    return resp

@app.route("/api/getuser")
def getuser():
    """

    +----------+------------------+
    |          | API Endpoint     |
    +==========+==================+
    | Endpoint | ``/api/getuser`` |
    +----------+------------------+
    | Method   | GET              |
    +----------+------------------+
    | Cookie   | **Yes**          |
    +----------+------------------+

    Gets the user associated with the given session cookie.

    Example curl request:

    .. code-block:: bash

        curl --cookie "session=b98071db4e4ff3e33b92d77647ec9d59" http://127.0.0.1:2004/api/getuser

    Example valid result JSON:

    .. code-block:: json

        {
            "email": "gae19jtu@uea.ac.uk", 
            "fname": "Eden", 
            "id_": 1, 
            "sname": "Attenborough"
        }

    """
    # args = flask.request.args.to_dict()
    user = authenticate()
    return user.serialize()

@app.route("/api/addarea", methods = ["POST"])
def addarea():
    """
    +----------+------------------+
    |          | API Endpoint     |
    +==========+==================+
    | Endpoint | ``/api/addarea`` |
    +----------+------------------+
    | Method   | POST             |
    +----------+------------------+
    | Cookie   | **Yes**          |
    +----------+------------------+

    Appends a mower area to the database. Example POST JSON:

    .. code-block:: json
        :linenos:

        {
            "name": "Besides the lake", 
            "notes": "Besides the lake, avoiding the trees, left of the pond", 
            "area_coords": [
                [52.619274360887445, 24.0, 1.2393361009732562], 
                [52.619274360423944, 24.0, 1.2393361009734234], 
                [52.61927259385035, 24.0, 1.2346346239823422]
            ], 
            "nogo_zones": [
                [
                    [52.619534542345434, 24.0, 1.2393352345423454], 
                    [52.61927234523454, 24.0, 1.2393234523452346], 
                    [52.62345423452346, 24.0, 1.2334523452345234]
                ], [
                    [52.619534542345434, 24.0, 1.2393352345423454], 
                    [52.61927234523454, 24.0, 1.2393234523452346], 
                    [52.62345423452346, 24.0, 1.2334523452345234]
                ]
            ]
        }

    A nice way to get this JSON is to use :func:`models.Area.serialize`. See
    :class:`models.Area` for an example model class instantiation.

    Example curl request:

    .. code-block:: bash

        curl --cookie "session=b98071db4e4ff3e33b92d77647ec9d59" -H "Content-Type: application/json" --request POST --data '{"name": "Besides the lake", "notes": "Notes", "area_coords": [], "nogo_zones": []}' http://127.0.0.1:2004/api/addarea

    Example successful JSON response:
    
    .. code-block:: json

        {
            "success": "Area 'Besides the lake' added"
        }

    """
    req = flask.request.json
    user = authenticate()
    try:
        area = models.deserialize(req, models.Area, owner = user)
    except Exception as e:
        return flask.abort(400, e.args)
    with database.MowerDatabase(host = db_host) as db:
        db.create_area(area)
    return {"success": "Area '%s' added" % area.name}

@app.route("/api/getareas")
def getareas():
    """
    +----------+------------------+
    |          | API Endpoint     |
    +==========+==================+
    | Endpoint | ``/api/getareas``|
    +----------+------------------+
    | Method   | GET              |
    +----------+------------------+
    | Cookie   | **Yes**          |
    +----------+------------------+

    Get a list of the areas associated with the current user. The areas
    are serialized to JSON (see :func:`models.Area.serialize`).

    Example curl request:

    .. code-block:: bash

        curl --cookie "session=53b5b4baaeb3d5ab8ce4a3dcfd346945" http://127.0.0.1:2004/api/getareas

    Example return JSON data:

    .. code-block:: json
        :linenos:

        {
            "areas": [
                {
                    "area_coords": [
                        [52.619274360887445, 24.0, 1.2393361009732562],
                        [52.619274360423944, 24.0, 1.2393361009734234],
                        [52.61927259385035, 24.0, 1.2346346239823422]
                    ],
                    "name": "Besides the lake",
                    "nogo_zones": [
                        [
                            [52.619534542345434, 24.0, 1.2393352345423454],
                            [52.61927234523454, 24.0, 1.2393234523452346],
                            [52.62345423452346, 24.0, 1.2334523452345234]
                        ],
                        [
                            [52.619534542345434, 24.0, 1.2393352345423454],
                            [52.61927234523454, 24.0, 1.2393234523452346],
                            [52.62345423452346, 24.0, 1.2334523452345234]
                        ]
                    ],
                    "notes": "Besides the lake, avoiding the trees, left of the pond"
                }
            ]
        }

    """
    user = authenticate()
    with database.MowerDatabase(host = db_host) as db:
        return {"areas": [area.serialize() for area in db.get_areas(user)]}

if __name__ == "__main__":
    try:
        if sys.argv[1] == "--production":
            waitress.serve(TransLogger(app), host = "0.0.0.0", port = 2005, threads = 4)
        else:
            app.run(host = "0.0.0.0", port = 2004, debug = True)
    except IndexError:
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
