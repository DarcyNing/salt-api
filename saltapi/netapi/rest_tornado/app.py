
import functools
import os
import json
import uuid 

import tornado
import yaml

import salt
import salt.auth
import salt.log
import saltapi

opts = salt.client.LocalClient().opts

sessionStore = {} 

def saltAuther(func):
    def _(handler,*args,**kwargs):
        cookie_id = handler.get_cookie('id')
        auth_token = sessionStore.get(cookie_id)
        print auth_token
        if not auth_token:
            return handler.write('auth token expire')
            
        handler.lowstate = { k:v[0]  for k,v in handler.request.arguments.items() }
        handler.lowstate['token'] = auth_token['token']
        handler.token = auth_token
        func(handler,*args,**kwargs)
    return _ 

def exec_lowstate(lowstate):
    if lowstate.get('token'):
        api = saltapi.APIClient(opts)
        res = api.run(lowstate)
        return res
    return 'auth token expire'

class Index(tornado.web.RequestHandler):
    def get(self):
        import inspect

        clients = [ name for name,_ in inspect.getmembers(saltapi.APIClient,predicate=inspect.ismethod) if not name.startswith('__')]
        clients.remove('run')
        
        out = json.dumps({
            'return': "Welcome",
            'clients': clients,
        })
        self.write(out)

    @saltAuther
    def post(self):
        self.write( json.dumps({
            'return':exec_lowstate(self.lowstate)
        }))


class Login(tornado.web.RequestHandler):

    def get(self):
        self.set_status(401) 
        self.set_header('WWW-Authenticate','Session')

    def post(self):
        auth = salt.auth.LoadAuth(opts)
        lowstate = { k:v[0]  for k,v in self.request.arguments.items() }
        token = auth.mk_token(lowstate)
        if not 'token' in token:
            self.set_status(401)
            return

        cookie_id = uuid.uuid4().hex
        self.set_header('X-Auth-Token',cookie_id) 
        self.set_cookie('id',cookie_id)
        sessionStore[cookie_id] = token    

        if token['name'] in opts['external_auth'][token['eauth']]:
            perms = opts['external_auth'][token['eauth']][token['name']]
        else:
            perms = opts['external_auth'][token['eauth']]['*']

        self.write(json.dumps({'return': [{
            'token': cookie_id,
            'expire': token['expire'],
            'start': token['start'],
            'user': token['name'],
            'eauth': token['eauth'],
            'perms': perms,
        }]}))

class Logout(tornado.web.RequestHandler):
    
    def get(self):
        self.clear_all_cookies()

        self.write(json.dumps( {'return': "Your token has been cleared"} ))


class Minion(tornado.web.RequestHandler):
    @saltAuther
    def get(self):
        mid = self.get_argument('mid',None)
        lowstate = {'client':'local','tgt':mid or '*','fun':'grains.items','token':self.token['token']}
        self.write(
            json.dumps({
                'return':exec_lowstate(lowstate)    
            })
        )

    @saltAuther
    def post(self):
        self.lowstate['client'] = 'local_async'
        job_data = exec_lowstate(self.lowstate)
        self.set_status(202)
        self.write(
            json.dumps(
                {
                    'return':job_data,
                }
            )
        )


class Jobs(tornado.web.RequestHandler):
    @saltAuther
    def get(self,jid=None):
        lowstate =  [{
            'client': 'runner',
            'fun': 'jobs.lookup_jid' if jid else 'jobs.list_jobs',
            'jid': jid,
            'token':self.lowstate['token']
        }]

        self.write(json.dumps(
            {'return':exec_lowstate(lowstate)}
        ))





