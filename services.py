import endpoints
import httplib2
import sql_queries
import logging

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from oauth2client.appengine import AppAssertionCredentials
from apiclient.discovery import build

BILLING_PROJECT_ID = "282649517306"
SCOPE = 'https://www.googleapis.com/auth/bigquery'
HTTP = AppAssertionCredentials(scope=SCOPE).authorize(httplib2.Http())
TIMEOUT = 10

# https://psa-dna-netbooster.appspot.com/_ah/api/uapsadata/v1/query?ref=global&dealer=abc&startDate=20140930&endDate=20141002

class Response(messages.Message):
    timexec = messages.StringField(1)
    res = messages.StringField(2)
    
class Request(messages.Message):
    ref = messages.StringField(1, required=True)
    dealer = messages.StringField(2, required=True)
    startDate = messages.StringField(3, required=True) 
    endDate = messages.StringField(4, required=True)

CONTAINER = endpoints.ResourceContainer(Request, 
                                        ref = messages.StringField(1, required=True))#,
                                        #startDate = messages.StringField(2, required=True),
                                        #endDate = messages.StringField(3, required=True))
  
@endpoints.api(name='uapsadata', version='v1', description='Return data from psa ua bq export')
class PsaBqApi(remote.Service):
    
    def __init__(self):
        self.bq_service = build('bigquery', 'v2', http=HTTP)
    
    def make_query_config(self, query):
        return {'query': query, 'timeoutMs': TIMEOUT, 'useQueryCache': False}
    
    @endpoints.method(Request, Response, http_method='GET')
    def query(self, request):
        query = sql_queries.easy[request.ref]      
        result = (self.bq_service.jobs().query(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (request.startDate, request.endDate, request.dealer))).execute())
        #timexec = str(long(result["statistics"]["endTime"]) - long(result["statistics"]["startTime"]))
        logging.debug(result)
        timexec = 0
        logging.debug(request.endDate)
        values = [str(r['f'][0]["v"]) for r in result['rows']][0]
        return Response(time=timexec, res=values)
          
application = endpoints.api_server([PsaBqApi])