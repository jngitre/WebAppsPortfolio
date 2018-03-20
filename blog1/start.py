import webapp2
import logging
import re
import jinja2
import os
import time

from google.appengine.ext import db

title=""
art=""
error=""
favorite=0
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

class MyHandler(webapp2.RequestHandler):
	def write(self, *writeArgs):    
		self.response.write(" : ".join(writeArgs))
	def render_str(self, template, **params):
		tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
		return tplt.render(params)
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class MainPage(MyHandler):
    def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		logging.info("********** MainPage GET **********")
		python_dictionary = {}   # creating a new dictionary
		self.render("ascii.html", **python_dictionary)

class Art(db.Model):
		created = db.DateTimeProperty(auto_now_add=True)
		titlea = db.TextProperty()
		arta = db.TextProperty()
		
class TestHandler(MyHandler):
	def render_ascii(self, **params):
		global title, art, error
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
		self.render("ascii.html", title = title, art=art, error=error, arts=arts)
	
	def post(self):
		global title, art, error, favorite
		title = self.request.get("title")
		art = self.request.get("art")
		things = {}
		things['art'] = art
		things['title'] = title
	
		if (title == "" or art == ""):
			error = "Need both a title and some artwork!"
		
		else:
			artas = Art()
			artas.titlea =title
			artas.arta = art
			artas.put()
			error = ""
			favorite = artas.key().id()
			
		things['error'] = error
		time.sleep(0.2)
		self.render_ascii(**things)
		
class Favorites(MyHandler):
	def get(self):
		global title, art, favorite
		art = Art.get_by_id(favorite)
		things = {}
		things['art'] = art.arta
		things['title'] = art.titlea
		logging.info(art.arta)
		self.render("favorite.html", **things)


application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/test', TestHandler),
	('/favorites', Favorites)
], debug=True)
