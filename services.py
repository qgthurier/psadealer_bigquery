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
TIMEOUT = 10000

# https://psa-dna-netbooster.appspot.com/_ah/api/uapsadata/v1/query?ref=global&dealer=abc&startDate=20140930&endDate=20141002

class Response(messages.Message):
    time = messages.StringField(1)
    res = messages.StringField(2)
    
class Request(messages.Message):
    ref = messages.StringField(1, required=True)
    dealer = messages.StringField(2, required=True)
    startDate = messages.StringField(3, required=True) 
    endDate = messages.StringField(4, required=True)
  
@endpoints.api(name='uapsadata', version='v1', description='Return data from psa ua bq export')
class PsaBqApi(remote.Service):
    
    def __init__(self):
        self.bq_service = build('bigquery', 'v2', http=HTTP)
    
    def make_query_config(self, query):
        return {'query': query, 'timeoutMs': TIMEOUT, 'useQueryCache': False}
    
    def parse_query_result(self, result):
        if int(result["totalRows"]) > 0:
            fields = result['schema']['fields']
            out = "\t".join([field['name'] for field in fields])
            for row in result['rows']:
                out += "\n" + "\t".join([row['f'][i]['v'] if row['f'][i]['v'] is not None else "None" for i in xrange(len(fields))])
        else:
            out = "no row"
        return out
    
    def get_query_timexec(self, id):
        res = self.bq_service.jobs().get(projectId=BILLING_PROJECT_ID, jobId=id).execute()
        return str(long(res["statistics"]["endTime"]) - long(res["statistics"]["startTime"]))
    
    @endpoints.method(Request, Response, http_method='GET')
    def query(self, request):
        query = sql_queries.easy[request.ref]      
        job = self.bq_service.jobs().query(projectId=BILLING_PROJECT_ID, body=self.make_query_config(query % (request.startDate, request.endDate, request.dealer))).execute()
        return Response(time=self.get_query_timexec(job['jobReference']['jobId']), res=self.parse_query_result(job))
          
application = endpoints.api_server([PsaBqApi])