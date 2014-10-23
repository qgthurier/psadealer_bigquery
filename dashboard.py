#!/usr/bin/env python
# coding: utf8 

import codecs
import httplib2
import logging
import os
import urllib
import json
import bqclient
import queries
import json

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

BILLING_PROJECT_ID = "282649517306"
SCOPE = 'https://www.googleapis.com/auth/bigquery'
HTTP = AppAssertionCredentials(scope=SCOPE).authorize(httplib2.Http())
MAXITER = 50

class Timeout(webapp2.RequestHandler):
    def get(self):
        self.response.write("at least one query has reached the time out !")
               
class Dashboard(webapp2.RequestHandler):
    
    def initialization(self):
        self.bq_service = build('bigquery', 'v2', http=HTTP)
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
  
    def get_query_val(self, id):
        result = self.bq_service.jobs().getQueryResults(projectId=BILLING_PROJECT_ID, jobId=id).execute()
        logging.debug(result)
        UTF8Writer = codecs.getwriter('utf8')
        if int(result["totalRows"]) > 0:
            fields = result['schema']['fields']
            out = "\t".join([field['name'] for field in fields])
            for row in result['rows']:
                out += "\n" + "\t".join([row['f'][i]['v'] if row['f'][i]['v'] is not None else "None" for i in xrange(len(fields))])
        else:
            out = "no row"
        return out
    
    def get(self):         
        # initialize parameters 
        self.initialization()
        # insert easy queries in the jobs queue       
        for metric, query in queries.easy.items():
            job = self.bq_service.jobs().insert(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (self.from_statement, self.par['dealer'], self.date_condition))).execute()
            logging.debug(query % (self.from_statement, self.par['dealer'], self.date_condition))
            self.query_ref.update({metric: job['jobReference']['jobId']})
        # insert tricky queries in the job queue
        query = queries.tricky['new_visitors']
        metric = 'new_visitors'
        job = self.bq_service.jobs().insert(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (self.par['startDate_str'], self.par['endDate_str'], self.par['startDate_str'], self.par['startDate_str']))).execute()
        logging.debug(query % (self.par['startDate_str'], self.par['endDate_str'], self.par['startDate_str'], self.par['startDate_str']))
        self.query_ref.update({metric: job['jobReference']['jobId']})
        # wait until all user's queries are done      
        reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()        
        i = 0
        variable = {}
        template = JINJA_ENVIRONMENT.get_template('template.html')
        while i <= MAXITER and len(self.query_ref.values()) > len(self.query_timexec.keys()):
            reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()
            for j in reply['jobs']:
                id = j['jobReference']['jobId'] 
                if id in self.query_ref.values() and j not in self.query_timexec.keys():
                    self.query_timexec.update({id: long(j["statistics"]["endTime"]) - long(j["statistics"]["startTime"])})
                    qry = self.query_ref.keys()[self.query_ref.values().index(id)]
                    variable.update({qry: "* " + qry + " - " + str(self.query_timexec[id]) + " ms * \n\n" + self.get_query_val(id)})
            i += 1          
        self.response.write(template.render(variable))

class Query(webapp2.RequestHandler):
    
    def initialization(self):
        self.bq_service = build('bigquery', 'v2', http=HTTP)
        self.par = self.parse_get_parameters()
        self.query_ref = {}
        self.query_timexec = {}
        self.from_statement = "(TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('" + self.par['startDate_str'] + "'), TIMESTAMP('" + self.par['endDate_str'] + "')))"
        self.date_condition = ""        
        
    def parse_get_parameters(self):
        get = cgi.FieldStorage()
        try:
          ref = get['ref'].value
        except:
          ref = 'global'
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
        return {'dealer': dealer, 'timeout': time_out, 'ref': ref, 
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
  
    def get_query_val(self, id):
        result = self.bq_service.jobs().getQueryResults(projectId=BILLING_PROJECT_ID, jobId=id).execute()
        logging.debug(result)
        UTF8Writer = codecs.getwriter('utf8')
        if int(result["totalRows"]) > 0:
            fields = result['schema']['fields']
            out = "\t".join([field['name'] for field in fields])
            for row in result['rows']:
                out += "\n" + "\t".join([row['f'][i]['v'] if row['f'][i]['v'] is not None else "None" for i in xrange(len(fields))])
        else:
            out = "no row"
        return out
    
    def get(self):         
        # initialize parameters 
        self.initialization()
        # insert easy queries in the jobs queue
        metric = self.par['ref']
        query = queries.easy['metric']      
        job = self.bq_service.jobs().insert(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (self.from_statement, self.par['dealer'], self.date_condition))).execute()
        logging.debug(query % (self.from_statement, self.par['dealer'], self.date_condition))
        self.query_ref.update({metric: job['jobReference']['jobId']})
        # wait until all user's queries are done      
        reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()        
        jobs_done = [j['jobReference']['jobId'] for j in reply['jobs']]
        i = 0
        while i <= MAXITER and job['jobReference']['jobId'] not in jobs_done:
            reply = self.bq_service.jobs().list(projectId=BILLING_PROJECT_ID, allUsers=False, stateFilter="done", projection="minimal", fields="jobs(jobReference,statistics)").execute()
            jobs_done = [j['jobReference']['jobId'] for j in reply['jobs']]
            i += 1
        for j in reply['jobs']:
            if job['jobReference']['jobId'] == j['jobReference']['jobId']:
                query_timexec = long(j["statistics"]["endTime"]) - long(j["statistics"]["startTime"])
                query_val = self.get_query_val(j['jobReference']['jobId'])
        variable = {time: str(query_timexec), res: query_val}
        self.response.headers['Content-Type'] = 'application/json'        
        self.response.out.write(json.dumps(variable))
         
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     ('/timeout', Timeout)
     ('/query', Query)
    ],
    debug=True)
