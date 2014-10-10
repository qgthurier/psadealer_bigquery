
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
time_out_reached = False
        
class Dashboard(webapp2.RequestHandler):
   
    def _get_ga_data(self, bqdata, metrics):
        global time_out_reached
        logging.info(metrics)
        logging.info(bqdata)
        out = None
        if bqdata['jobComplete']:
            out = bqdata["rows"][0]["f"][0]["v"]
        else:
            time_out_reached = True
        return out

    @decorator.oauth_required
    def get(self):
        global startDate, endDate, vue, dealer, time_out_reached
        
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
                DT_COND = "and dt >= timestamp('" + startDate_str + "') and dt <= timestamp('" + endDate_str + "')"
                
            QUERY = ("select sum(totals.visits) as val,"
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)
            logging.info(QUERY)      
            visites_item = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "visits") 
            if not visites_item:
                visites_item = 0
            
            QUERY = ("select count(distinct(fullVisitorId)) as val,"
                   "from %s "
                   "WHERE lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)
            logging.info(QUERY)    
            visitors_item = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "visitors")  
            if not visitors_item:
                visitors_item = 0
            
            QUERY = ("select avg(totals.pageviews) as val,"
                    "from %s "
                    "where trafficSource.medium = 'organic'"
                    "and lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)
            logging.info(QUERY)
            item_page_visite = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "pages") 
             
            QUERY = ("select sum(totals.bounces)/count(*) as val,"
                   "from %s "
                   "WHERE lower(trafficSource.referralPath) contains '%s' %s") % (FROM, dealer, DT_COND)
            logging.info(QUERY)
            item_bounce = self._get_ga_data(bq.Query(QUERY, BILLING_PROJECT_ID, time_out), "bounce")  
              
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
            
            logging.info(time_out_reached)
            if not time_out_reached:
                template = JINJA_ENVIRONMENT.get_template('management.html')
                self.response.write(template.render(variables))
            else:
                self.response.write("at least one query reached the time out!")

        else: 
           self.redirect(users.create_login_url("/"))
            
app = webapp2.WSGIApplication(
    [
     ('/', Dashboard),
     (decorator.callback_path, decorator.callback_handler())
    ],
    debug=True)
