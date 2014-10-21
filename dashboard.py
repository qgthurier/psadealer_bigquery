
#!/usr/bin/env python

import httplib2
import logging
import os
import urllib
import json
import bqclient
import queries

from datetime import date, timedelta, datetime
from apiclient.discovery import build
from oauth2client import appengine
from oauth2client import client
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2
import cgi 

from Base import Basehandler
      
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=[
      'https://www.googleapis.com/auth/bigquery'
    ])

BILLING_PROJECT_ID = "282649517306"

class Timeout(webapp2.RequestHandler):
    def get(self):
        self.response.write("at least one query has reached the time out !")
               
class Dashboard(webapp2.RequestHandler):
    
    def initialize(self):
        self.app.config['bq_service'] = build('bigquery', 'v2')
        self.app.config['par'] = self.parse_get_parameters()
        self.app.config['query_ref'] = {}
        if self.app.config['par']['source'] == "tables":
            self.app.config['from_statement'] = "(TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('" + self.par['startDate_str'] + "'), TIMESTAMP('" + self.par['endDate_str'] + "')))"
            self.app.config['date_condition'] = ""
        elif self.app.config['par']['source'] == "view":
            self.app.config['from_statement'] = "[87581422.view]"
            self.app.config['date_condition'] = "and dt >= timestamp('" + self.par['startDate_str'] + "') and dt <= timestamp('" + self.par['endDate_str'] + "')"
        
    def parse_get_parameters(self):
        get = cgi.FieldStorage()
        try:
          dealer = get['dealer'].value
        except:
          dealer = 'ajaccio'
        try:
          time_out = get['time_out'].value
        except:
          time_out = 100
        try:  
          source = get['source'].value
        except:
          source = "tables"
        try:
          startDate_str = get['startDate'].value
          startDate = datetime.strptime(startDate_str, '%Y%m%d')
        except:
          startDate = datetime.today() - timedelta(30)
          startDate_str = startDate.strftime('%Y%m%d')
        try:
          endDate_str = get['endDate'].value   
          endDate = datetime.strptime(endDate_str, '%Y%m%d')
        except:
          endDate =  datetime.today() - timedelta(1)
          endDate_str = endDate.strftime('%Y%m%d')
        self.par = {'dealer': dealer, 'timeout': time_out, 
                    'source':source, 'startDate': startDate, 
                    'endDate': endDate, 'startDate_str': startDate_str, 'endDate_str': endDate_str} 
    
    def make_query_config(self, query):
        return {'configuration': {'query': {'query': query,'useQueryCache': False}}}
        
    def get_metric_timexec(self, id):
        res = self.bq_service.jobs().getQueryResults(projectId=BILLING_PROJECT_ID, jobId=id).execute(decorator.http())
        return str(long(res["statistics"]["endTime"]) - long(res["statistics"]["startTime"]))
            
    def get_metric_val(self, id):
        res = self.bq_service.jobs().getQueryResults(projectId=BILLING_PROJECT_ID, jobId=id).execute(decorator.http())
        return [str(r['f'][0]["v"]) for r in res['rows']][0] 

    @decorator.oauth_required
    def get(self):        
        user = users.get_current_user()         
        if user:                
            for metric, query in queries.list.items():
                job = service.jobs().insert(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (self.from_statement, self.par['dealer'], self.date_condition))).execute(decorator.http())
                logging.debug(query % (self.from_statement, self.par['dealer'], self.date_condition))
                self.query_ref.update({metric: job['jobReference']['jobId']})        
            reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal",maxResults=len(query_ref), fields="jobs/jobReference").execute(decorator.http())        
            job_done = set([j['jobReference']['jobId'] for j in reply['jobs']])
            while len(set(self.query_ref.values()) - job_done) > 0:
                reply = service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs/jobReference").execute(decorator.http())
                job_done = set([j['jobReference']['jobId'] for j in reply['jobs']])
                
            '''              
            visites_item = self._get_ga_data(bq1.Query(QUERY, BILLING_PROJECT_ID, time_out), "visits") 
            if not visites_item:
                visites_item = 0   
            visitors_item = self._get_ga_data(bq2.Query(QUERY, BILLING_PROJECT_ID, time_out), "visitors")  
            if not visitors_item:
                visitors_item = 0
            item_page_visite = self._get_ga_data(bq3.Query(QUERY, BILLING_PROJECT_ID, time_out), "pages") 
            item_bounce = self._get_ga_data(bq4.Query(QUERY, BILLING_PROJECT_ID, time_out), "bounce")  
              
            variables = {
                'url': decorator.authorize_url(),
                'has_credentials': decorator.has_credentials(),
                'get':get,
                'visites_item': visites_item,
                'visitors_item' : visitors_item,
                'item_bounce':item_bounce,
                'item_page_visite':item_page_visite,
                'dealer':dealer,
                'startDate':startDate,
                'endDate':endDate,
                }

            template = JINJA_ENVIRONMENT.get_template('management.html')
            self.response.write(template.render(variables))
            '''    
            logging.debug(reply) 
            logging.debug(query_ref)
            out = [] 
            for metric, id in query_ref.items():            
                out.append([metric + ": " + self.get_metric_val(id) + " (" + self.get_metric_timexec(id) + " ms)"])
            
            self.response.write(out)
            
        else: 
           self.redirect(users.create_login_url("/"))
            
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     ('/timeout', Timeout),
     (decorator.callback_path, decorator.callback_handler())
    ],
    debug=True)
