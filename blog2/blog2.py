import webapp2
import re
import logging
import jinja2
import os
from google.appengine.ext import db
import random, string
import hashlib
import hmac

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

entered_username = ""
entered_password_1 = ""
entered_password_2 = ""
entered_email = ""
USERNAME_RE = re.compile("^([a-zA-Z0-9\-\_]{3,20})$")
PASSWORD_RE = re.compile("^(.{3,20})$")
EMAIL_RE = re.compile("^(.+?)\@(.+?)\.(.+?)")

class MyHandler(webapp2.RequestHandler):
	def write(self, *writeArgs):    
		self.response.write(" : ".join(writeArgs))
		
	def render_str(self, template, **params):
		tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
		return tplt.render(params)
		
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
		
	def write_form(self, entered_email="", entered_username="", u_error="", p_error="", e_error="", v_error="", u_error2=""):
		template_values = {"emaila": entered_email,
							"usera": entered_username,
							"user": u_error,
							"pass": p_error, 
							"email": e_error, 
							"verify": v_error,
							"user2": u_error2}
		template = JINJA_ENVIRONMENT.get_template('templates/signup.html')
		self.response.write(template.render(template_values))
		
	def hash_str(self, s):
		h = str(hmac.new("salty", s).hexdigest())
		return h
	
	def make_secure_val(self, s):
		return str(str(s) + "|" + self.hash_str(s))
	
	def check_secure_val(self, h):
		s = h.split('|')
		if (self.make_secure_val(s[0]) == h):
			return s[0]
		else:
			return None
			
	def make_salt(self):
		for i in range(25):
			return ''.join(random.choice(string.lowercase))
			
	def make_pw_hash(self, name, pw, salt=None):
		if not(salt):
			salt=self.make_salt()
		h = self.hash_str(str(name)+str(pw)+str(salt))
		return str(h + "|" + salt)
	
	def valid_pw(self, name, pw, h):
		salt = h.split('|')
		if (salt[1]):
			if(h == make_pw_hash(name, pw, salt[1])):
				return True
		else:
			return False
		
class MainPage(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.write_form()

class User(db.Model):
	user = db.StringProperty()
	hashedpass = db.StringProperty()
	email = db.StringProperty()
		
class TestHandler(MyHandler):
	def post(self):
		global entered_username, entered_password_1, entered_password_2, entered_email
		u_error = ""
		p_error = ""
		v_error = ""
		e_error = ""
		u_error2 = ""
		
		entered_username = self.request.get("username")
		entered_password_1 = self.request.get("password")
		entered_password_2 = self.request.get("verify")
		entered_email = self.request.get("email")
		username = self.valid_user()
		password = self.valid_pass()
		email = self.valid_email()
		
		u = User()
		u.hashedpass = self.make_pw_hash(entered_username, entered_password_1, "salty")
		logging.info(u.hashedpass)
		u.user = entered_username
		u.email = entered_email
		u.put()
		
		f_user = db.GqlQuery("SELECT user FROM User")
		for i in f_user:
			if(i.user == entered_username):
				u_error2 = "That username is taken"
		
		if(not username):
			u_error = "Invalid username"
			u_error2 = ""
		if(not password):
			p_error = "Invalid password"
		if(entered_password_1 != entered_password_2):
			v_error = "Passwords don't match"
		if(not email):
			e_error = "Invalid email address"
			
		self.write_form(entered_email, entered_username, u_error, p_error, e_error, v_error, u_error2)
		
		if(u_error == "" and p_error=="" and e_error== "" and v_error=="" and u_error2==""):
			user_id = self.request.cookies.get('user_id','')
			id = u.key().id()
			hashed = self.make_secure_val(str(id))
			self.response.headers.add_header("Set-Cookie", "user_id=%s; Path=/" % hashed)
			self.redirect("/welcome")
		
	def valid_user(self):
		global entered_username
		return bool(USERNAME_RE.match(entered_username))
		
	def valid_pass(self):
		global entered_password_1
		return bool(PASSWORD_RE.match(entered_password_1))
		
	def valid_email(self):
		global entered_email
		if (entered_email == ""):
			return True
		else:
			return bool(EMAIL_RE.match(entered_email))
		
class WelcomePage(MyHandler):
	def write_welcome(self):
		user_id = self.request.cookies.get('user_id')
		if(self.check_secure_val(user_id)):
			user = User.get_by_id(int(self.check_secure_val(user_id)))
			template_values = {"user": user.user}
			template = JINJA_ENVIRONMENT.get_template('templates/welcome.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect("/login")
	def get(self):
		self.write_welcome()
		
class LoginPage(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.render("login.html")

class LoginSubmitted(MyHandler):
	def post(self):
		usern = self.request.get("username")
		passn = self.request.get("password")
		f_user = db.GqlQuery("SELECT user FROM User")
		for i in f_user:
			if(i.user == usern):
				logging.info(i.hashedpass)
				logging.info(self.make_pw_hash(usern, passn, "salty"))
				if(self.valid_pw(usern, passn, i.hashedpass)):
					id = i.key().id()
					hashed = self.make_secure_val(id)
					self.response.headers.add_header("Set-Cookie", "user_id=%s; Path=/" % hashed)
					self.redirect("/welcome")
			else:
				self.render("login.html", error="Invalid login")
		
application = webapp2.WSGIApplication([
	('/', MainPage), 
	('/signup', TestHandler),
	('/welcome', WelcomePage),
	('/login', LoginPage),
	('/loggedin', LoginSubmitted)
], debug = True)