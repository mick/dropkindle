import redis



class DKDataModel:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, db=2)
    def saveuerauth(self, username, authkey, authsecret):
        self.r.set(username + ":authkey", authkey)
        self.r.set(username + ":authsecret", authsecret)

    def getuserauth(self, username):
        key = self.r.get(username+":authkey")
        secret = self.r.get(username+":authsecret")
        return {"key":key, "secret":secret}

    def getfilebyid(self, id):
        username = self.r.get(id+":username")
        path = self.r.get(id+":path")
        return {"username":username, "path":path}

    def savefile(self, username, path):
        count = self.r.incr("files")
        self.r.set(str(count) + ":username", username)
        self.r.set(str(count) + ":path", path)
        return str(count)

