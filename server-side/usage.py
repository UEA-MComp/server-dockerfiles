import requests
import models
import json
import os

scheme = "http"
host = "mower.awiki.org"
port = 2006
# host = "127.0.0.1"
# port = 2004

session = requests.Session()


if not os.path.exists(".cookies.json"):
    # either sign in or create an account (comment out one or the other)

    # sign in if no cookies are found, then save the cookies
    r = session.post("%s://%s:%d/api/signin" % (scheme, host, port), json = {
        "email": "gae19jtu@uea.ac.uk", "fname": "Eden", "sname": "Attenborough", "pass": "floofleberries"
    })

    # r = session.post("%s://%s:%d/api/adduser" % (scheme, host, port), json = {
    #     "email": "gae19jtu@uea.ac.uk", "fname": "Eden", "sname": "Attenborough", "pass": "floofleberries"
    # })

    with open(".cookies.json", "w") as f:
        json.dump(r.cookies.get_dict(), f)

    print(r.content.decode())

with open(".cookies.json", "r") as f:
    cookies = json.load(f)

r = session.get("%s://%s:%d/api/getuser" % (scheme, host, port), cookies = cookies)
print(r.status_code)
print(r.content.decode())

area = models.Area(
    owner = None, 
    name = "Besides the lake", 
    notes = "Besides the lake, avoiding the trees, left of the pond", 
    area_coords = [
        (52.619274360887445, 24.0, 1.2393361009732562),
        (52.619274360423945, 24.0, 1.2393361009734234),
        (52.619272593850345, 24.0, 1.2346346239823423)
    ], 
    nogo_zones = [
        [
            (52.619534542345435, 24.0, 1.2393352345423454),
            (52.619272345234545, 24.0, 1.2393234523452345),
            (52.623454234523454, 24.0, 1.2334523452345234)
        ],
        [
            (52.619534542345435, 24.0, 1.2393352345423454),
            (52.619272345234545, 24.0, 1.2393234523452345),
            (52.623454234523454, 24.0, 1.2334523452345234)
        ]
    ]
)

# print(json.dumps(area.serialize(), indent = 4))
# ser = area.serialize()
# print(models.deserialize(ser, models.Area, owner = None))

# r = session.post("%s://%s:%d/api/addarea" % (scheme, host, port), cookies = cookies, json = area.serialize())
# print(r.status_code)
# print(r.content.decode())

r = session.get("%s://%s:%d/api/getareas" % (scheme, host, port), cookies = cookies)
print(r.status_code)
# print(r.content.decode())
print(json.dumps(r.json(), indent=4))