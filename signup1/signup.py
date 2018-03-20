import webapp2
import re
import logging

entered_username = ""
entered_password_1 = ""
entered_password_2 = ""
entered_email = ""
USERNAME_RE = re.compile("^([a-zA-Z0-9\-\_]{3,20})$")
PASSWORD_RE = re.compile("^(.{3,20})$")
EMAIL_RE = re.compile("^(.+?)\@(.+?)\.(.+?)")


signup_form = """
  <head>
    <meta charset="utf-8">
    <title>Signup Page</title>
    <link rel="stylesheet" type="text/css" href="stylesheets/signup.css">
  </head>
  <body>
    <h1>Signup</h1>
    <form method="post" action="/test">
      <table>
        <tr>
          <td class="label">Username</td>
          <td><input type="text" name="username" value=""></td>
          <td class="error" value="">%(u_error)s</td>
        </tr>

        <tr>
          <td class="label">Password</td>
          <td><input type="password" name="password" value=""></td>
          <td class="error" value="">%(p_error)s</td>
        </tr>

        <tr>
          <td class="label">Verify Password</td>
          <td><input type="password" name="verify" value=""></td>
          <td class="error" value="">%(v_error)s</td>
        </tr>

        <tr>
          <td class="label">Email (optional)</td>
          <td><input type="text" name="email" value=""></td>
          <td class="error" value="">%(e_error)s</td>
        </tr>
      </table>

      <input type="submit">

    </form>
  </body>
"""

		
class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.write_form()
	def write_form(self, u_error="", p_error="", e_error="", v_error=""):
		self.response.write(signup_form % {"u_error": u_error, "p_error": p_error, "e_error": e_error, "v_error": v_error})
	
class TestHandler(webapp2.RequestHandler):
	def post(self):
		global entered_username, entered_password_1, entered_password_2, entered_email
		u_error = ""
		p_error = ""
		v_error = ""
		e_error = ""
		entered_username = self.request.get("username")
		entered_password_1 = self.request.get("password")
		entered_password_2 = self.request.get("verify")
		entered_email = self.request.get("email")
		username = self.valid_user()
		password = self.valid_pass()
		email = self.valid_email()
		if(not username):
			u_error = "Invalid username"
		if(not password):
			p_error = "Invalid password"
		if(entered_password_1 != entered_password_2):
			v_error = "Passwords don't match"
		if(not email):
			e_error = "Invalid email address"
		
		self.write_form(u_error, p_error, e_error, v_error)
		if(u_error == "" and p_error=="" and e_error== "" and v_error==""):
			self.redirect("/welcome")
		
	def valid_user(self):
		global entered_username
		logging.info(entered_username)
		return bool(USERNAME_RE.match(entered_username))
		
	def valid_pass(self):
		global entered_password_1
		logging.info(entered_password_1)
		return bool(PASSWORD_RE.match(entered_password_1))
		
	def valid_email(self):
		global entered_email
		if (entered_email == ""):
			return True
		else:
			return bool(EMAIL_RE.match(entered_email))

	def write_form(self, u_error="", p_error="", e_error="", v_error=""):
		logging.info(u_error)
		logging.info(p_error)
		self.response.write(signup_form % {"u_error": u_error, "p_error": p_error, "e_error": e_error, "v_error": v_error})
		
class WelcomePage(webapp2.RequestHandler):
	def write_welcome(self):
		global entered_username
		self.response.write("""<title>Welcome Page</title><body><h1> Welcome, %(username)s!</h1><image src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/2000px-Smiley.svg.png"></body>""" % {"username": entered_username})
	def get(self):
		self.write_welcome()
		
application = webapp2.WSGIApplication([
	('/', MainPage), 
	('/test', TestHandler),
	('/welcome', WelcomePage)
], debug = True)