
#!/usr/bin/env python


import httplib2
import logging
import os
import urllib
import json
import bqclient

from datetime import date, timedelta, datetime
from apiclient import discovery
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
    ],
    cache=memcache)

BILLING_PROJECT_ID = "282649517306"

tables = ["[87581422.ga_sessions_20141009]","[87581422.ga_sessions_20141008]",
"[87581422.ga_sessions_20141007]","[87581422.ga_sessions_20141006]","[87581422.ga_sessions_20141005]", 
"[87581422.ga_sessions_20141004]","[87581422.ga_sessions_20141003]","[87581422.ga_sessions_20141002]",
"[87581422.ga_sessions_20141001]","[87581422.ga_sessions_20140930]"]


datetimes = [datetime.strptime(tab.split("_")[2][:-1], '%Y%m%d') for tab in tables]
mem = memcache.Client()

class Dashboard(webapp2.RequestHandler):
   
    def _get_ga_data(self, bqdata, metrics):
        logging.info(metrics)
        logging.info(bqdata)
        out = bqdata["rows"][0]["f"][0]["v"]
        return out

    @decorator.oauth_required
    def get(self):
        global startDate, endDate, vue, dealer
        
        get = cgi.FieldStorage()
        try:
          dealer = get['dealer'].value
        except:
          dealer = 'ajaccio'
        try:
          ndays = int(get['ndays'].value)
        except:
          ndays = len(tables)
        try:
          time_out = get['time_out'].value
        except:
          time_out = 100
        try:  
          source = get['source'].value
        except:
          source = "tables"
        try:
          startDate_str = get['dateStart'].value
          startDate = datetime.combine(date.strptime(startDate_str, '%Y%m%d'), datetime.min.time())
        except:
          startDate = datetime.combine(date.today() - timedelta(30), datetime.min.time())
          startDate_str = startDate.strftime('%Y%m%d')
        try:
          endDate_str = get['endDate'].value   
          endDate = datetime.combine(endDate_str, datetime.min.time())
        except:
          endDate =  datetime.combine(date.today() - timedelta(1), datetime.min.time())
          endDate_str = endDate.strftime('%Y%m%d')

        selected_tabs = [tables[i] for i, dt in enumerate(datetimes) if startDate <= dt <= endDate]   
        user = users.get_current_user()
        
        if user: 
            
            get = cgi.FieldStorage()
            bq = bqclient.BigQueryClient(decorator)
            
            if source == "tables":
                FROM = ",".join(selected_tabs)
                DT_COND = ""
            elif source == "view":
                FROM = "[87581422.view]"
                DT_COND = "and timestamp('" + startDate_str + "') <= dt <= timestamp('" + endDate_str + "')"
            
            QUERY = ("select sum(totals.visits) as val,"
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)      
            visites_item = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "visits")
            logging.info(QUERY) 
            
            QUERY = ("select count(distinct(fullVisitorId)) as val,"
                   "from %s "
                   "WHERE lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)    
            visitors_item = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "visitors")  
            logging.info(QUERY) 
            
            QUERY = ("select avg(totals.pageviews) as val,"
                    "from %s "
                    "where trafficSource.medium = 'organic'"
                    "and lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)
            item_page_visite = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "pages")
            logging.info(QUERY) 
             
            QUERY = ("select sum(totals.bounces)/count(*) as val,"
                   "from %s "
                   "WHERE lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND) 
            item_bounce = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "bounce")  
            logging.info(QUERY) 
              
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
            

        else: # if the user is not logged in yet, redirection to the google sign in form
           self.redirect(users.create_login_url("/"))
            
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     (decorator.callback_path, decorator.callback_handler())
    ],
    debug=True)
