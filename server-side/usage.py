import requests

scheme = "http"
host = "127.0.0.1"
port = 2004

session = requests.Session()

r = session.post("%s://%s:%d/api/signin" % (scheme, host, port), data = {
    "email": "gae19jtu@uea.ac.uk", "fname": "Eden", "sname": "Attenborough", "pass": "password"
})

print(r.content)