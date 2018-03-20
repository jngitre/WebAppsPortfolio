import webapp2
import re
import logging
import jinja2
import os
from google.appengine.ext import db
import random, string
import hashlib
import hmac
import time
import datetime
from xml.dom import minidom
import urllib2
import json
from google.appengine.api import memcache

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
		template_values = {"emaila": entered_email, "usera": entered_username, "user": u_error, "pass": p_error, 
							"email": e_error, "verify": v_error, "user2": u_error2}
		template = JINJA_ENVIRONMENT.get_template('templates/signup.html')
		self.response.write(template.render(template_values))
	def render_blog(self, **params):
		blogg = top_posts()
		user_id = self.request.cookies.get('user_id')
		if(self.valid_cookie()):
			user = self.valid_cookie().user
		else:
			user=""
		self.render("blog.html", blogg=blogg[0], user=user)
		
	def hash_str(self, s):
		h = str(hmac.new("salty", s).hexdigest())
		return h
	def make_secure_val(self, s):
		return str(str(s) + "|" + self.hash_str(s))
	def check_secure_val(self, h):
		if(h):
			s = h.split('|')
			if (self.make_secure_val(s[0]) == h):
				return s[0]
			else:
				return None
		else:
			return None		
	def make_salt(self):
		salt = ""
		for i in range(25):
			salt = salt.join(random.choice(string.lowercase))
			logging.info(salt)
		return salt		
	def make_pw_hash(self, name, pw, salt=None):
		if(not salt):
			salt=self.make_salt()
		h = self.hash_str(str(name)+str(pw)+str(salt))
		return str(h + "|" + str(salt))
	def valid_pw(self, name, pw, h):
		salt = h.split('|')
		if (salt[1]):
			if(h == self.make_pw_hash(name, pw, salt[1])):
				return True
		else:
			return False
	def valid_cookie(self):
		user_id = self.request.cookies.get('user_id')
		if(self.check_secure_val(user_id)):
			user = User.get_by_id(int(self.check_secure_val(user_id)))
			return user
		else:
			return False
	def get_coords(self, ip):
		if (ip):
			p = urllib2.urlopen("https://www.freegeoip.net/xml/%s" % ip)
			x=minidom.parseString(p.read())
			lat = x.getElementsByTagName('Latitude')[0].childNodes[0].nodeValue
			lon = x.getElementsByTagName('Longitude')[0].childNodes[0].nodeValue
			tup = tuple([lat, lon])
			return db.GeoPt(lat, lon)
		else:
			return None
	def render_json(self, d):
		json_txt = json.dumps(d)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.write(json_txt)
		
	def cookie_expire(self):
		user_id = self.request.cookies.get('user_id')
		nowTime = datetime.datetime.utcnow()
		expireTime = nowTime + datetime.timedelta(days=2)
		self.response.set_cookie('user_id', str(user_id), expires=expireTime, path='/')
	
def mc_set(key, val):
	mc = (val, datetime.datetime.utcnow())
	memcache.set(key, mc)
	return None

def top_posts():
	blog = mc_get("top10")
	logging.info(blog)
	if blog != (None, 0):
		logging.info(">>>CACHE HIT<<<")
		return blog
	else:
		blogs = db.GqlQuery("SELECT * FROM Blog "
                   "ORDER BY created DESC "
				   "Limit 10" )
		logging.info(">>> DATABASE ACCESS <<<")
		mc_set("top10", list(blogs))
		return (list(blogs), 0)
		
def mc_get(key):
	if memcache.get(key):
		got = memcache.get(key)
		logging.info(got)
		age = datetime.datetime.utcnow() - got[1]
		return (got[0], age.seconds)
	else:
		return (None, 0)
	
class MainPage(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.write_form()
		self.cookie_expire()
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
		self.cookie_expire()
		
		if(u_error == "" and p_error=="" and e_error== "" and v_error=="" and u_error2==""):
			user_id = self.request.cookies.get('user_id','')
			u = User()
			u.hashedpass = str(self.make_pw_hash(entered_username, entered_password_1))
			u.user = entered_username
			u.email = entered_email
			u.put()
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
		

class User(db.Model):
	user = db.StringProperty()
	hashedpass = db.TextProperty()
	email = db.StringProperty()
		
class WelcomePage(MyHandler):
	def write_welcome(self):
		self.cookie_expire()
		if(not self.valid_cookie()):
			self.render("login.html")
		else:
			self.redirect("/blog")
	def get(self):
		self.write_welcome()
		self.cookie_expire()
		
class Blog(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	content = db.TextProperty()
	subject = db.TextProperty()
	coords = db.GeoPtProperty()
	
	def as_dict(self):
		time_fmt = '%c'
		d = {'subject': self.subject,
			 'content': self.content,
			 'created': self.created.strftime(time_fmt)}
		return d
		
class BlogPage(MyHandler):
	def get(self):
		self.cookie_expire()
		if(self.request.url.endswith('.json')):
			blogs =  db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC limit 10")
			list = []
			for blog in blogs:
				list.append(blog.as_dict())
			self.render_json(list)
		else:
			self.render_blog()
		
		
class LoginPage(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.render("login.html")
		
	def post(self):
		usern = self.request.get("username")
		passn = self.request.get("password")
		f_user = db.GqlQuery("SELECT * FROM User")
		
		for i in f_user:
			if(i.user == usern):
				if(self.valid_pw(usern, passn, i.hashedpass)):
					id = i.key().id()
					hashed = self.make_secure_val(str(id))
					self.response.headers.add_header("Set-Cookie", "user_id=%s; Path=/" % hashed)
					self.redirect("/blog")
			else:
				self.render("login.html", error="Invalid login")
		
class Logout(MyHandler):
	def get(self):
		self.response.headers.add_header("Set-Cookie", "user_id=; Path=/")
		self.redirect("/blog")
		

class NewPost(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		user_id = self.request.cookies.get('user_id')
		self.cookie_expire()
		if(self.valid_cookie()):
			user = self.valid_cookie().user
			self.render("newpost.html", user=user)
		else:
			self.redirect("/blog")
	def post(self):
		global subject, content, error, submitted, ip
		subject = self.request.get("subject")
		content = self.request.get("content")
		self.cookie_expire()
		if(self.request.get("ip")):
			ip = self.request.get("ip")
		else:
			ip = self.request.remote_addr
		logging.info(ip)
		logging.info(self.request.remote_addr)
		things = {}
		things['subject'] = subject
		things['content'] = content
		
		if (subject == "" or content == ""):
			error = "Please provide both a subject and content"
		
		else:
			blogg = Blog()
			blogg.subject = subject
			blogg.content = content
			if not(ip):
				ip = None
			blogg.coords = self.get_coords(ip)
			blogg.createdtext = blogg.created.date().strftime("%A %B %d, %Y") + " " + blogg.created.time().strftime("%X")
			logging.info(blogg.created.date().strftime("%A %B, %d"))
			blogg.put()
			memcache.delete("top10")
			error = ""
			submitted = blogg.key().id()
			self.redirect("/blog/" + str(submitted))
		
		if(self.valid_cookie()):
			user = self.valid_cookie().user
		
		things['error'] = error
		things['user'] = user
		time.sleep(0.2)
		self.render("newpost.html", **things)
		error=""
		
class Permalinked(MyHandler):
	def get(self, submitted):
		self.cookie_expire()
		if(self.valid_cookie()):
			user = self.valid_cookie().user
			post = Blog.get_by_id(int(submitted))
			self.render("permalink.html", post=post, user=user)
		else:
			user=""
			self.redirect("/blog")

class BlankSlate(MyHandler):
	def get(self):
		self.redirect("/blog")
		
class MapPage(MyHandler):
	def get(self):
		self.cookie_expire()
		if(self.valid_cookie()):
			user = self.valid_cookie().user
		else:
			user=""
		blogs =  db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC limit 10")
		src = "http://maps.googleapis.com/maps/api/staticmap?size=800x600&sensor=false"
		for blog in blogs:
			if (blog.coords):
				src += "&markers=" + str(blog.coords.lat) + "," + str(blog.coords.lon)
		self.render("map.html", blogg=blogs, user=user, src=src)
		

application = webapp2.WSGIApplication([
	('/', BlankSlate),
	('/signup', MainPage), 
	('/welcome', WelcomePage),
	('/login', LoginPage),
	('/logout', Logout),
	(r'/blog/?(?:\.json)?', BlogPage),
	(r'/blog/newpost/?', NewPost),
	(r'/blog/(\d+)(?:\.json)?', Permalinked),
	(r'/blog/map/?', MapPage)
	], debug = True)