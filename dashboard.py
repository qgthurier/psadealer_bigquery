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
from oauth2client.appengine import AppAssertionCredentials

import webapp2
import jinja2
import cgi 
      
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

'''
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=[
      'https://www.googleapis.com/auth/bigquery'
    ])
'''

BILLING_PROJECT_ID = "282649517306"
SCOPE = 'https://www.googleapis.com/auth/bigquery'
credentials = AppAssertionCredentials(scope=SCOPE)
http = credentials.authorize(httplib2.Http())

class Timeout(webapp2.RequestHandler):
    def get(self):
        self.response.write("at least one query has reached the time out !")
               
class Dashboard(webapp2.RequestHandler):
    
    def initialization(self):
        self.bq_service = build('bigquery', 'v2', http=http)
        self.par = self.parse_get_parameters()
        self.query_ref = {}
        self.query_timexec = {}
        if self.par['source'] == "tables":
            self.from_statement = "(TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('" + self.par['startDate_str'] + "'), TIMESTAMP('" + self.par['endDate_str'] + "')))"
            self.date_condition = ""
        elif self.par['source'] == "view":
            self.from_statement = "[87581422.view]"
            self.date_condition = "and dt >= timestamp('" + self.par['startDate_str'] + "') and dt <= timestamp('" + self.par['endDate_str'] + "')"
        
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
        return {'dealer': dealer, 'timeout': time_out, 
                    'source':source, 'startDate': startDate, 
                    'endDate': endDate, 'startDate_str': startDate_str, 'endDate_str': endDate_str} 
    
    def make_query_config(self, query):
        return {'configuration': {'query': {'query': query,'useQueryCache': False}}}
        
    def get_metric_timexec(self, id):
        res = self.bq_service.jobs().get(projectId=BILLING_PROJECT_ID, jobId=id).execute(decorator.http())
        return str(long(res["statistics"]["endTime"]) - long(res["statistics"]["startTime"]))
            
    def get_metric_val(self, id):
        res = self.bq_service.jobs().getQueryResults(projectId=BILLING_PROJECT_ID, jobId=id).execute()
        return [str(r['f'][0]["v"]) for r in res['rows']][0] 


    #@decorator.oauth_required
    
    def get(self):        
        #user = users.get_current_user()         
        #if user: 
        # initialize parameters 
        self.initialization()
        # insert queries in the jobs queue       
        for metric, query in queries.list.items():
            job = self.bq_service.jobs().insert(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (self.from_statement, self.par['dealer'], self.date_condition))).execute()
            logging.debug(query % (self.from_statement, self.par['dealer'], self.date_condition))
            self.query_ref.update({metric: job['jobReference']['jobId']})
            self.query_timexec.update({job['jobReference']['jobId']: 0})
        # wait until all user's queries are done      
        reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()        
        job_done = set([j['jobReference']['jobId'] for j in reply['jobs']])
        i = 0
        while i <= self.app.config.get('maxIter') and len(set(self.query_ref.values()) - job_done) > 0:
            reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()
            job_done = set([j['jobReference']['jobId'] for j in reply['jobs']])
            i += 1          
        '''              
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
        # calculate time execution for each query
        for j in reply['jobs']:
            if j['jobReference']['jobId'] in self.query_ref.values():
                self.query_timexec[j['jobReference']['jobId']] = long(j["statistics"]["endTime"]) - long(j["statistics"]["startTime"])
        # add debug information    
        logging.debug(reply) 
        logging.debug(self.query_ref)
        logging.debug(self.query_timexec)
        out = [metric + ": " + self.get_metric_val(id) + " (" + str(self.query_timexec[id]) + " ms)" for metric, id in self.query_ref.items()]
        self.response.write(out)     
        #else: 
          # self.redirect(users.create_login_url("/"))
            
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     ('/timeout', Timeout),
     #(decorator.callback_path, decorator.callback_handler())
    ],
    debug=True,
    config={'maxIter': 50})
