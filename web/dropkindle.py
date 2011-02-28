import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.web
import tornado.escape
import sys, os
from DKDataModel import DKDataModel
import json, dropbox.client, dropbox.auth
from oauth import oauth

DROPBOX_API = "https://api.dropbox.com/0/"

CACHE_DATA = False
DropKindleData =  DKDataModel()
config = dropbox.auth.Authenticator.load_config("../dropbox.ini")


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    def get(self):
        self.render("templates/index.html", title="DropKindle")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")

class LoginHandler(BaseHandler):
    def get(self):

        msg = ""
        if(self.get_argument("status", "") == "fail"):
            msg = "Your username / password were not right... try again?"

        self.render("templates/login.html", title="DropKindle - Login", message=msg)


    def post(self):
        self._db_auth(self.get_argument("username"), self.get_argument("password"))

    def _db_auth(self, username, password):
        auth =  dropbox.auth.Authenticator(config)

        try:
            token = auth.obtain_trusted_access_token(username, password)
        except:
            print(sys.exc_info()[0])
            #Login failed.
            self.redirect("/login?status=fail")
            return


        DropKindleData.saveuerauth(username, token.key, token.secret)
        self.set_secure_cookie("user", username)
        self.redirect("/files")

    def on_response(self, response):
        if response.error: raise tornado.web.HTTPError(500)
        json = tornado.escape.json_decode(response.body)
        self.write(response.body)
        self.finish()

class FileHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        auth =  dropbox.auth.Authenticator(config)
        savedauth = DropKindleData.getuserauth(tornado.escape.xhtml_escape(self.current_user))
        token = oauth.OAuthToken(savedauth['key'], savedauth['secret'])
        dbox = dropbox.client.DropboxClient("api.dropbox.com", "api-content.dropbox.com", 80, auth, token)
        res = dbox.metadata("dropbox", "/Kindle")
        files = json.loads(res.body)

        self.render("templates/files.html", title="Drop Kindle - Files", contents=files['contents'])

class DownloadFileHandler(BaseHandler):
    def get(self, path):
        if not self.current_user:
            self.redirect("/login")
            return
        auth =  dropbox.auth.Authenticator(config)
        savedauth = DropKindleData.getuserauth(tornado.escape.xhtml_escape(self.current_user))
        token = oauth.OAuthToken(savedauth['key'], savedauth['secret'])
        dbox = dropbox.client.DropboxClient("api.dropbox.com", "api-content.dropbox.com", 80, auth, token)
        print "path: /"+path
        res = dbox.get_file("dropbox", "/"+path)
        contents =  res.read()
        self.set_header("Content-Type", "application/octet-stream")
        self.write(contents)
        #res = dbox.metadata("dropbox", "/Kindle")
        #links = json.loads(res.body)
        #self.write(links)

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYasdfasdfjasfdLKSJekef",
    "reload_modified_templates":True
    }
application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/files", FileHandler),
        (r"/file/(.*)", DownloadFileHandler),

        ], **settings)

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


