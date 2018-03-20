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
submitted=0

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
	def render_newpost(self, **params):
		global content, subject, error
		self.render("newpost.html", content = content, subject = subject, error=error)
	def render_blog(self, **params):
		blogg = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC limit 10")
		self.render("blog.html", blogg=blogg)

class Blog(db.Model):
		created = db.DateTimeProperty(auto_now_add=True)
		content = db.TextProperty()
		subject = db.TextProperty()
		
class TestHandler(MyHandler):
	def get(self):
		self.render_blog()

class NewPost(MyHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.render("newpost.html")

class NewPosted(MyHandler):
	def post(self):
		global subject, content, error, submitted
		subject = self.request.get("subject")
		content = self.request.get("content")
		things = {}
		things['subject'] = subject
		things['content'] = content
		
		if (subject == "" or content == ""):
			error = "Please provide both a subject and content"
		
		else:
			blogg = Blog()
			blogg.subject = subject
			blogg.content = content
			blogg.createdtext = blogg.created.date().strftime("%A %B %d, %Y") + " " + blogg.created.time().strftime("%X")
			logging.info(blogg.created.date().strftime("%A %B, %d"))
			blogg.put()
			error = ""
			submitted = blogg.key().id()
			self.redirect("/blog/" + str(submitted))
			
		things['error'] = error
		time.sleep(0.2)
		self.render_newpost(**things)
		error=""
		
class Permalinked(MyHandler):
	def get(self, submitted):
		post = Blog.get_by_id(int(submitted))
		logging.info(submitted)
		self.render("permalink.html", post=post)
		
application = webapp2.WSGIApplication([
    ('/', NewPost),
	(r'/blog/?', TestHandler),
	(r'/blog/newpost/?', NewPosted),
	(r'/blog/(\d+)', Permalinked)
], debug=True)
