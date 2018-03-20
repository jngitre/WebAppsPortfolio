import webapp2
import cgi

def escape_html(s):
		return cgi.escape(s, quote = True)
		
		
form = """ <div> 
<h2>What is your birthday?</h2>
<form method="post" action="/validate">
<label> Month
<input type="text" name = "month" value="%(month)s"> </label>
<br>
<label> Day
<input type="text" name = "day" value="%(day)s"> </label>
<br>
<label> Year
<input type="text" name = "year" value="%(year)s"> </label>
<br> <br>
<input type="submit">
</form>
<div>%(error)s</div>
</div>
"""

form2 = """ <div style="padding: 200px"> 
<h2 style="text-align: center; color:  #98AFC7" >What is your birthday?</h2>
<form style = "text-align:center; font-family:Arial" method="post" action="/validate">
<label> Month
<input type="text" name = "month" value="%(month)s"> </label>
<br>
<label> Day
<input type="text" name = "day" value="%(day)s"> </label>
<br>
<label> Year
<input type="text" name = "year" value="%(year)s"> </label>
<br> <br>
<input type="submit" style="background-color: #98AFC7; color: white; border: none; padding: 5px 10px 5px 10px">
</form>
<div style="text-align: center; font-family: Arial; color: #E74C3C">%(error)s</div>
</div>
"""
month=""
day=""
year="" 

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.write_form()
			
	def write_form(self, error="", month="", day="", year=""):
		self.response.write(form2 % {"error": error, "month": month, "day": day, "year": year})
		

class TestHandler(webapp2.RequestHandler):
	def post(self):
		global month
		global day
		global year
		month = self.request.get("month")
		day = self.request.get("day")
		year = self.request.get("year")
		month = escape_html(month)
		year = escape_html(year)
		day = escape_html(day)
		if(self.valid_day() and self.valid_month() and self.valid_year()):
			self.redirect("/success")
		else:
			self.write_form("That's not a real date. Try again!", month, day, year)
	
	def valid_day(self):
		global day
		if(day.isdigit()):
			if(int(day) <= 31 and int(day) >= 1):
				return True
			else:
				return False
		else:
			return False
			
	def valid_month(self):
		global month
		if(month[:3] == "Jan" or month[:3] == "Feb" or month[:3] == "Mar" or month[:3] == "Apr" or month[:3] == "May" or month[:3] == "Jun" or month[:3] == "Jul" or month[:3] == "Aug" or month[:3] == "Sep" or month[:3] == "Nov" or month[:3] == "Dec"):
			return True
		else:
			return False
			
	def valid_year(self):
		global year
		if(year.isdigit()):
			if(int(year) <= 2016 and int(year) >= 1900):
				return True
			else:
				return False
		else:
			return False
			
	def write_form(self, error="", month="", day="", year=""):
		self.response.write(form2 % {"error": error, "month": month, "day": day, "year": year})
	
class SuccessPage(webapp2.RequestHandler):
	def get(self):
		self.response.write("""<h1 style = "color: #98AFC7; padding: 250px; text-align: center">Thanks for submitting your birthday!<h1>""")
		
application = webapp2.WSGIApplication([
	('/', MainPage), 
	('/validate', TestHandler),
	('/success', SuccessPage)
], debug = True)