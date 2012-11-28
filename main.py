# VapURL - Expiring URL service.
# Copyright (c) 2009 Aaron McBride and John Lawlor
# MIT License (see LICENSE.txt)
# https://github.com/nogwater/vapurl

import os
import re
import cgi
import random
import datetime
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from django.utils import simplejson
from models import VapUrl
from models import ErrorMessage
from models import Counter
import config

class MainHandler(webapp.RequestHandler):

    def post(self):
        """Supports the creation of new VapURLs"""
    
        template_data = {
            'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.'),
            'url':'http://'
        }
        self.createVapUrl(template_data)
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_data))
        
    def get(self):
        """Show main page, create a new VapURL, or redirect."""
    
        template_data = {
            'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.'),
            'url':'http://'
        }
        name = self.request.path[1:]
        if len(name) > 0:         #redirect if needed
            self.redirectByName(name)
        else:                     #create if needed    
            self.createVapUrl(template_data)
        
        vapurlController = VapurlController()
        vapurlController.cleanup()
    
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_data))
                
    
    def createVapUrl(self, template_data):
        """Creates a VapURL based on the URL passed in as an argument.  Updates template_data."""
        url = self.request.get('url')
        if url != None and url != "":
            vapurlController = VapurlController()
            
            url = vapurlController.sanitize_url(url)            
            template_data['url'] = url
                
            max_time = self.request.get('max_time')
            custom_time = self.request.get('custom_time')
            try:
                max_time = int(max_time)
            except:
                max_time = 60
                self.logError("max_time not an int")
            
            if max_time == -1: #Custom Max
                try:
                    max_time = 1440 * int(custom_time.replace(',',''))
                    if max_time < 0 or int(custom_time.replace(',','')) > 1000:
                      max_time = 60
                except:
                    max_time = 60
                    self.logError("custom max_time not an int")
            else:
                if max_time not in [1 , 60, 1440, 10080]: #keep approved list? or make range?
                    max_time = 60
            
            max_visits = self.request.get('max_visits')
            custom_visits = self.request.get('custom_visits')
            
            try:
                max_visits = int(max_visits)
            except:
                max_visits = 1                
                self.logError("max_visits not an int")
            
            if max_visits == -1: #Custom Max
                try:
                    max_visits = int(custom_visits.replace(',',''))
                    if max_visits < 0 or int(custom_visits.replace(',','')) > 1000000:
                      max_visits = 60
                except:
                    max_visits = 60
                    self.logError("custom max_visits not an int")
            else:
                if max_visits not in [1, 5, 10, 25, 50, 100]: #keep approved list? or make range?
                    max_visits = 60
            
            vapUrl = vapurlController.create(url, max_time, max_visits)
            if vapUrl != None:                
                template_data['vapurl'] = config.baseURL + vapUrl.name
                template_data['name'] = vapUrl.name
                template_data['visits_remaining'] = vapUrl.visits_remaining
                template_data['exp_datetime'] = vapUrl.exp_datetime
            else:
                self.logError("error creating VapUrl. probably a bad URL:" + url)
                # probably BadValueError: Invalid URL: url
        
    def redirectByName(self, name):
        destination = None
        
        vapUrls = VapUrl.all()
        vapUrls.filter('name =', name)
        vapUrls.filter('vaporized =', False)
        vapUrls.filter('exp_datetime >=', datetime.datetime.now())
        # can't use more than one inequality filter :(
        #vapUrls.filter('visits_remaining >', 0)
        
        if vapUrls.count() > 0:
            vapUrl = vapUrls[0]
            if vapUrl.visits_remaining > 0:
                destination = vapUrl.link
                vapUrl.visits_remaining -= 1
                vapUrl.put()
            
        if destination == None:
            destination = '/' # we didn't go anywhere, so let's go home
        else:    
            counters = Counter.all()
            counters.filter('type = ', 'visits/alltime')
            if counters.count() > 0:
                counter = counters[0]
                #TODO: make transactional
                counter.count += 1
                counter.put()
            else:
                counter = Counter()
                counter.type = 'visits/alltime'
                counter.count = 1
                counter.put()

        self.redirect(destination)
    
    def logError(self, error_text):
        errorMsg = ErrorMessage()
        errorMsg.text = error_text
        errorMsg.put()

class VapurlController:
    def sanitize_url(self, url):
        if url.find('http://http://') == 0 or url.find('http://https://') == 0:
            url = url[7:] # remove 'http://'
        if url.find('://') == -1:
            url = 'http://' + url
        url = url[:1024] # trim if long
        return url
    
    def cleanup(self):
        """Marks dead entries as vaporized"""
        #update data model
        #todo: remove this after the data model has been upgraded
        #vapUrls = VapUrl.all()
        #for vapUrl in vapUrls:
        #    if vapUrl.vaporized == None:
        #        vapUrl.vaporized = False
        #        vapUrl.put()
        
        # timed out
        vapUrls = VapUrl.all()
        vapUrls.filter('vaporized =', False)
        vapUrls.order('exp_datetime')
        vapUrls.filter('exp_datetime <', datetime.datetime.now())
        for vapUrl in vapUrls:
            vapUrl.vaporized = True
            vapUrl.put()
            
        # visited out
        vapUrls = VapUrl.all()
        vapUrls.filter('vaporized =', False)
        vapUrls.order('visits_remaining')
        vapUrls.filter('visits_remaining <', 1)
        for vapUrl in vapUrls:
            vapUrl.vaporized = True
            vapUrl.put()
            
    def create(self, url, max_time, max_visits):
        """Creates a new VapUrl and returns it if successful"""
        random.seed(str(random.random()) + url)
        name = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz-0123456789') for i in range(10)])
        
        vapUrl = None
        try:
            vapUrl = VapUrl()
            vapUrl.name = name
            vapUrl.link = db.Link(url)
            vapUrl.vaporized = False
            vapUrl.exp_datetime = datetime.datetime.now() + datetime.timedelta(minutes=max_time)
            vapUrl.visits_max = max_visits
            vapUrl.visits_remaining = max_visits
            vapUrl.put()
        except:
            vapUrl = None
        
        if vapUrl != None:
            counters = Counter.all()
            counters.filter('type = ', 'creates/alltime')
            if counters.count() > 0:
                counter = counters[0]
                #TODO: make transactional
                counter.count += 1
                counter.put()
            else:
                counter = Counter()
                counter.type = 'creates/alltime'
                counter.count = 1
                counter.put()
        return vapUrl;

class HelpHandler(webapp.RequestHandler):
    def get(self):
    
        template_data = {
            'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/help.html')
        self.response.out.write(template.render(path, template_data))

class AboutHandler(webapp.RequestHandler):
    def get(self):
    
        template_data = {
            'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/about.html')
        self.response.out.write(template.render(path, template_data))

class InfoHandler(webapp.RequestHandler):
    def get(self):
        template_data = {
            'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.')
        }
        
        vapurlController = VapurlController()
        vapurlController.cleanup()
        
        name = self.request.get('id')
        vapUrls = VapUrl.all()
        vapUrls.filter('name =', name)
        if vapUrls.count() > 0:
            vapUrl = vapUrls[0]
            template_data['have_info'] = True
            template_data['name'] = vapUrl.name
            template_data['create_datetime'] = vapUrl.create_datetime
            template_data['exp_datetime'] = vapUrl.exp_datetime
            if vapUrl.visits_max:
                template_data['visits_used'] = (vapUrl.visits_max - vapUrl.visits_remaining)
            else:
                template_data['visits_used'] = 'unknown'
            template_data['visits_remaining'] = vapUrl.visits_remaining
                
        path = os.path.join(os.path.dirname(__file__), 'templates/info.html')
        self.response.out.write(template.render(path, template_data))
            

class ApiHandler(webapp.RequestHandler):
    def get(self):
        request_path = self.request.path.lower()
        if request_path == '/api/create' or request_path == '/api/create/':
            self.create()
        else:
            template_data = {
                'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.')
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/api.html')
            self.response.out.write(template.render(path, template_data))
            
    def post(self):
        request_path = self.request.path.lower()
        if request_path == '/api/create' or request_path == '/api/create/':
            self.create()
        else:
            template_data = {
                'version': os.environ['CURRENT_VERSION_ID'][:os.environ['CURRENT_VERSION_ID'].rfind('.')].replace('-','.')
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/api.html')
            self.response.out.write(template.render(path, template_data))
    
    def create(self):
        """Parses input params, creates a vapurl, and prints the result as JSON."""
        result = {}
    
        try:
            url = self.request.get('url')
            minutes = int(self.request.get('minutes'))
            visits = int(self.request.get('visits'))
            
            if url == None or url == "":
                result['error'] = "url is missing"
            elif minutes < 1 or minutes > 1440000:
                result['error'] = "minutes is out of range"
            elif visits < 1 or visits > 1000000:
                result['error'] = "visits is out of range"
            else:
                vapurlController = VapurlController()
                url = vapurlController.sanitize_url(url)
                vapUrl = vapurlController.create(url, minutes, visits)
                if vapUrl != None:
                    result['id'] = vapUrl.name
                else:
                    result['error'] = "problem creating vapurl"
        except:
            result['error'] = "problem parsing parameters"
            
        self.response.out.write(simplejson.dumps(result))

def main():
    application = webapp.WSGIApplication([('/help', HelpHandler),
                                          ('/api', ApiHandler),
                                          ('/api/create', ApiHandler),
                                          ('/about', AboutHandler),
                                          ('/info.*', InfoHandler),
                                          ('/.*', MainHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
