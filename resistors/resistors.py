import webapp2
import logging
import re
import cgi
import jinja2
import os
import hmac

from google.appengine.ext import db

NAME_RE = re.compile("(.+?\ .+?){1}")

# Color names aranged by value (index=value)
COLORS = [
    'black',
    'brown',
    'red',
    'orange',
    'yellow',
    'green',
    'blue',
    'violet',
    'grey',
    'white']

# Multipliers in a dictionary, organized by value for ease of reading
MULTIPLIER = {
    1e0:    'black',
    1e1:    'brown',
    1e2:    'red',
    1e3:    'orange',
    1e4:    'yellow',
    1e5:    'green',
    1e6:    'blue',
    1e7:    'violet'}


# RGB Color Codes
COLORCODES = {
    "black":    "#000000",
    "brown":    "#a52a2a",
    "red":      "#ff0000",
    "orange":   "#ffa500",
    "yellow":   "#ffff00",
    "green":    "#008000",
    "blue":     "#0000ff",
    "violet":   "#800080",
    "grey":     "#808080",
    "white":    "#ffffff",
    "silver":   "#c0c0c0",
    "gold":     "#d4a017"}


def getColors(num):
    # To-be return value
    returnVals = []
    failReturnVals = [COLORS[0], COLORS[0], MULTIPLIER[1e0]]
    # Process the number
    indexPlaceholder = 0
    numStr = str(num)
    bandValues = ""
    indexPlaceholder = 2
    bandValues = numStr[:indexPlaceholder]
    # If there's 4 stripes
    if (num / float(bandValues)) % 10:
        indexPlaceholder = 3
        bandValues = numStr[:indexPlaceholder]
    # If there's a third band to add
    if len(numStr) > indexPlaceholder:
        if numStr[indexPlaceholder] != "0":
            bandValues = numStr[:indexPlaceholder + 1]
    # Needs another black band
    if len(bandValues) < 2:
        bandValues = bandValues + "0"
    for value in bandValues:
        if value == ".":
            continue
        returnVals.append(COLORS[int(value)])
    returnVals.append(MULTIPLIER[round(num / float(bandValues.replace(".", "")), 2)])
    return returnVals


#List of colors (strings) to ohms (float)
def getOhms(colors):
    bandValues = ""
    multiply = 0
    # Get the index numbers of the colors
    while len(colors) > 1:
        bandValues = bandValues + str(COLORS.index(colors.pop(0)))
    # Find the key (multiplier) based on color (no easy way to do this)
    for key, value in MULTIPLIER.items():
        if value == colors[0]:
            multiply = key
            break
    # Color value * multiplier
    return float(bandValues) * multiply

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
    ## saves you from having to type self.response.out.write
    def write(self, a):            
        self.response.out.write(a)
    
    ## takes a template and dictionary and returns a string with the rendered template
    def render_str(self, template, **params): 
	template = JINJA_ENVIRONMENT.get_template('templates/'+template)
        return template.render(params)

    ## takes a template and dictionary and writes the rendered template
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

SECRET="imsosecret"
def hash_str(s):
   return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
   return s+'|'+hash_str(s)

def check_secure_val(h):
   val = h.split('|')[0]
   if (h == make_secure_val(val)):
		return val
		
def name_valid(h):
	return bool(NAME_RE.match(h))

class MainPage(Handler):
	def get(self):
		title1 = "Web Applications Midterm"
		title2 = "Good Luck"
		self.render("front.html",
					place_holder1=title1,
					place_holder2=title2)
	def post(self):
		title1 = "Web Applications Midterm"
		title2 = "Good Luck"
		name = self.request.get('name')
		error = ""
		if(name_valid(name)):
			first = name.split(' ')[0]
			last = name.split(' ')[1]
			hashed = make_secure_val(first+ "+" + last)
			self.response.headers.add_header("Set-Cookie", "myUser=%s; Path=/" % str(hashed))
			self.redirect('/resistor')
		else:
			error = "Please enter a first and a last name"
		self.render("front.html",
					place_holder1=title1,
					place_holder2=title2,
					err=error)
					
class Resistor(Handler):
	def get(self):
		self.render("resistor.html")
	def post(self):
		f_b = self.request.get('fb')
		s_b = self.request.get('sb')
		t_b = self.request.get('tb')
		m = self.request.get('m')
		bands = [f_b, s_b, t_b, m]
		resistance = int(getOhms(bands))
		self.render("resistor.html",colors=COLORS, 
									valf=f_b, vals=s_b, 
									valt=t_b, valm=m, 
									resist=resistance)
					
application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/resistor', Resistor)
], debug=True)
