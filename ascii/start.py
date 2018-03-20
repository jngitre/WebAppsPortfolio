import webapp2
import logging
import re
import jinja2
import os

from google.appengine.ext import db

title=""
art=""
error=""

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
	def render_ascii(self, template, **params):
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
		self.render("ascii.html", title = title, art=art, error=error, arts=arts)
		

class MainPage(MyHandler):
    def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		logging.info("********** MainPage GET **********")
		value1_in_program = "world series"
		value2_in_program = "Let's go Cardinals."
		python_dictionary = {}   # creating a new dictionary
		python_dictionary['title'] = value1_in_program
		python_dictionary['art'] = value2_in_program
		self.render("ascii.html", **python_dictionary)

class Art(db.Model):
		datea = db.datetime.datetime.now().date()
		timea = db.datetime.datetime.now().time()
		titlea = db.StringProperty()
		arta = db.StringProperty()
		logging.info(str(datea) + str(timea) + str(titlea) + str(arta))
		
class TestHandler(MyHandler):
	def post(self):
		global title
		global art
		title = self.request.get("title")
		art = self.request.get("art")
		things = {}
		things['art'] = art
		things['title'] = title
	
		logging.info(art)
		logging.info(title)
		if (title == "" or art == ""):
			things['error'] = "Need both a title and some artwork!"
			arts = Art(titlea = title, arta = art)
			things['arts'] = arts
		self.render_ascii("ascii.html", **things)


application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/test', TestHandler)
], debug=True)
