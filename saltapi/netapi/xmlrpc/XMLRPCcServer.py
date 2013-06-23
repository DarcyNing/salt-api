#!/usr/bin/python
#encoding=utf-8

import uuid,json
import argparse
import xmlrpclib
import salt.auth,saltapi
from SimpleXMLRPCServer import SimpleXMLRPCServer

opts = salt.client.LocalClient().opts

class Salter(object):

    def login(self,username,password,eauth='pam'):
        auth = salt.auth.LoadAuth(opts)
        token = auth.mk_token({'username':username,'password':password,'eauth':eauth})
        if not 'token' in token:
            return 'authentication failed'


        if token['name'] in opts['external_auth'][token['eauth']]:
            perms = opts['external_auth'][token['eauth']][token['name']]
        else:
            perms = opts['external_auth'][token['eauth']]['*']

        print 'salt token',token

        return {
            'token': token['token'],
            'expire': token['expire'],
            'start': token['start'],
            'user': token['name'],
            'eauth': token['eauth'],
            'perms': perms,
        }

    def lowstate(self,lowstate):
        res = self._exec_lowstate(lowstate)
        return json.dumps(res)

    def _exec_lowstate(self,lowstate):
        if lowstate.get('token'):
            api = saltapi.APIClient(opts)
            res = api.run(lowstate)
            return res
        return 'authentication required'

class SessionXMLRPCServer(SimpleXMLRPCServer):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, help='server port',default=18009)
    parser.add_argument('-i', type=str,help='ipaddress listened',default='0.0.0.0')
    args = parser.parse_args()

    args = parser.parse_args()
    server = SimpleXMLRPCServer((args.i,args.p))
    api = Salter()
    server.register_function(api.login, "login")
    server.register_function(api.lowstate, "lowstate")
    server.serve_forever()
