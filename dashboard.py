
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

tables = ["[87581422.ga_sessions_20141019]",
"[87581422.ga_sessions_20141018]","[87581422.ga_sessions_20141017]","[87581422.ga_sessions_20141016]",
"[87581422.ga_sessions_20141015]","[87581422.ga_sessions_20141014]","[87581422.ga_sessions_20141013]",
"[87581422.ga_sessions_20141012]","[87581422.ga_sessions_20141011]","[87581422.ga_sessions_20141010]",
"[87581422.ga_sessions_20141009]","[87581422.ga_sessions_20141008]",
"[87581422.ga_sessions_20141007]","[87581422.ga_sessions_20141006]","[87581422.ga_sessions_20141005]", 
"[87581422.ga_sessions_20141004]","[87581422.ga_sessions_20141003]","[87581422.ga_sessions_20141002]",
"[87581422.ga_sessions_20141001]","[87581422.ga_sessions_20140930]"]

datetimes = [datetime.strptime(tab.split("_")[2][:-1], '%Y%m%d') for tab in tables]
query_ref = {}

class Timeout(webapp2.RequestHandler):
    def get(self):
        self.response.write("at least one query has reached the time out !")
               
class Dashboard(webapp2.RequestHandler):
    
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
          
        return {'dealer': dealer, 'timeout': time_out, 'source':source, 'startDate': startDate, 'endDate': endDate} 
    
    def make_query_config(self, query):
        return {'configuration': {'query': {'query': query,'useQueryCache': False}}}
        
    def get_metric_timexec(self, reply, metric):
        global query_ref
        '''logging.info("job complete : " + str(bqdata['jobComplete']))
        if bqdata['jobComplete']:
            out = bqdata["rows"][0]["f"][0]["v"]
        else:
            time_out_reached = True
            self.redirect("/timeout")'''
        for job in reply["jobs"]:
            if job[id] == query_ref[metric]:
                return job["statistics"]["endTime"] - job["statistics"]["startTime"]

    @decorator.oauth_required
    def get(self):
        par = self.parse_get_parameters()
        selected_tabs = [tables[i] for i, dt in enumerate(datetimes) if par['startDate'] <= dt <= par['endDate']]   
        user = users.get_current_user()      
        
        if user: 
            
            service = build('bigquery', 'v2')                   
            if source == "tables":
                FROM = ",".join(selected_tabs)
                DT_COND = ""
            elif source == "view":
                FROM = "[87581422.view]"
                DT_COND = "and dt >= timestamp('" + startDate_str + "') and dt <= timestamp('" + endDate_str + "')"
            
            for metric, query in queries.list.items():
                job = service.jobs().insert(projectId=project, body=self.make_query_config(query)).execute()
                query_ref.update({metric: job['jobReference']['jobId']})
                
            reply = service.jobs().list(projectId=project, allUsers=False, stateFilter="done", projection="minimal")        
            while len(reply.jobs) < len(queries.list.items()):
                reply = service.jobs().list(projectId=project, allUsers=False, stateFilter="done", projection="minimal")
            
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
            out = []
            
            for job in reply["jobs"]:
                out.append(job["statistics"]["endTime"] - job["statistics"]["startTime"])
            
            self.response.write(template.render(out))
            
        else: 
           self.redirect(users.create_login_url("/"))
            
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     ('/timeout', Timeout),
     (decorator.callback_path, decorator.callback_handler())
    ],
    debug=True)
