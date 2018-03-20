import webapp2
import logging
import re
import cgi
import jinja2
import os
import hashlib

from google.appengine.ext import db

## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
   if template_name is None or '.' not in template_name:
      return False
      ext = template_name.rsplit('.', 1)[1]
      return ext in ('html', 'htm', 'xml')

JINJA_ENVIRONMENT = jinja2.Environment(
   autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoescaping
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class Handler(webapp2.RequestHandler):
	def write(self, *items):
		self.response.write(" : ".join(items))
	
	def render_str(self, template, **params):
		tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
		return tplt.render(params)
		
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
	
	def hash_str(self, s):
		h = str(hashlib.md5(s).hexdigest())
		return h
	
	def make_secure_val(self, s):
		return str(str(s) + "|" + self.hash_str(s))
	
	def check_secure_val(self, h):
		s = h.split('|')
		if (self.make_secure_val(s[0]) == h):
			return s[0]
		else:
			return None
			

class MainPage(Handler):

	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		lastvisit = 0
		visits = self.request.cookies.get('visits', self.make_secure_val('0'))
		if(self.check_secure_val(visits)):
			if(self.check_secure_val(visits).isdigit()):
				lastvisit = int(self.check_secure_val(visits))
				visits = int(self.check_secure_val(visits)) + 1	
				self.render("visits.html", visits=lastvisit + 1)
		else:
			visits = self.make_secure_val("-2")
			self.render("warning.html")
		
		if(int(lastvisit) >= 1000):
			self.render("congrats.html")
			
	
		visits = self.make_secure_val(str(lastvisit + 1))
		self.response.headers.add_header("Set-Cookie", "visits=%s" % str(visits))

	def post(self):
		logging.info("DBG: MainPage POST")

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
