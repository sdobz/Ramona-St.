#!/usr/bin/python
# The main index page of the system

import library.web as web
import applications

render = web.template.render('templates/index')

class index:
    def GET(self):
        bodyhtml = '' 
        for app in applications.applications:
            result=render.application(app.pretty_name,app.url,app.description)
            bodyhtml+=str(result)
        return render.index(render.head(),render.body(bodyhtml))

