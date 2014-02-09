import jinja2
import logging
import os
import random
import webapp2

from google.appengine.ext import db
from google.appengine.api import urlfetch 

jinja_env = jinja2.Environment( loader = jinja2.FileSystemLoader(
    os.path.dirname(__file__)))


class Doge(db.Model):
  name = db.StringProperty()
  picture = db.BlobProperty(default=None)


class MainHandler(webapp2.RequestHandler):
  def get(self):
    name = self.request.get('name')
    if name == '':
      name = 'World'

    suggestions = self.getSomeRandomNames()
    suggestion_str = ' '.join(suggestions)

    template = jinja_env.get_template('index.html')
    template_values = {
       'title': 'So jpg. Very doge. Wow.',
       'name': name,
       'suggestions': suggestion_str
    }
    output_text = template.render(template_values)
    self.response.write(output_text)

  def getSomeRandomNames(self):
    result = db.GqlQuery("SELECT * FROM Doge LIMIT 50").fetch(50)
    n = len(result)
    if n > 0:
      doggies = random.sample(result, min(n, 10))
      return [d.name for d in doggies]
    return []
 

class ImageHandler(webapp2.RequestHandler):
  def get(self):
    name = self.request.get('name')
    if name != '':
      doge = self.getDoge(name)
      if doge != None and doge.picture != None:
        self.response.headers['Content-Type'] = "image/jpeg"
        self.response.out.write(doge.picture)
        return
    self.redirect('/static/doge.jpg')

  def getDoge(self, name):
    # normalize before retrieval
    name = name.lower()
    result = db.GqlQuery("SELECT * FROM Doge WHERE name = :1 LIMIT 1",
      name).fetch(1)
    if len(result) > 0:
      return result[0]
    else:
      return None 


class UploadHandler(webapp2.RequestHandler):
  def post(self):
    name = self.request.get('name')
    url = self.request.get('url')

    if name == '' or url == '':
      logging.error('User did not submit name or url for new doge.')
      self.response.out.write('ERROR: Please submit a name and a valid img url.')
      return
    # Normalize the name before storing in db
    name = name.lower()
    my_doge = Doge(name=name)

    # Try to fetch a picture
    result = urlfetch.fetch(url)
    status = result.status_code
    content_type = result.headers['content-type'] 
    if status == 200 and content_type == 'image/jpeg':
      my_doge.picture = result.content
    else:
      logging.error('Failed to fetch a jpeg. No pic associated with ' + name)

    my_doge.put()
    self.response.out.write('SUCCESS')

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/upload', UploadHandler),
                               ('/img', ImageHandler),
                               ], debug=True)
