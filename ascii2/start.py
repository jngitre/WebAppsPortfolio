import webapp2
import logging
import re
import jinja2
import os
import time

from google.appengine.ext import db

subject=""
blog=""
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
		self.render("blog.html", **python_dictionary)

class Blog(db.Model):
		created = db.DateTimeProperty(auto_now_add=True)
		content = db.TextProperty()
		subject = db.TextProperty()
		
class TestHandler(MyHandler):
	def render_ascii(self, **params):
		global title, art, error
		arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
		self.render("blog.html", title = title, art=art, error=error, arts=arts)
	
	def post(self):
		
		
class NewPost(MyHandler):
	def post(self):
		global subject, blog, error, favorite
		subject = self.request.get("subject")
		blog = self.request.get("blog")
		things = {}
		things['subject'] = subject
		things['blog'] = blog
	
		if (subject == "" or blog == ""):
			error = "Please provide both a subject and content"
		
		else:
			blogg = Blog()
			blogg.subject = subject
			blogg.content = blog
			blogg.put()
			error = ""
			submitted = blogg.key().id()
			
		things['error'] = error
		time.sleep(0.2)
		self.render_ascii(**things)


application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/blog', '/blog/', TestHandler),
	('/blog/newpost', '/blog/newpost/', NewPost)
], debug=True)
