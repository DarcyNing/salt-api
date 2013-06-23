
import xmlrpclib

def test_server():
    server = xmlrpclib.Server('http://192.168.1.215:18009')
    res = server.login('salt','1q2w3e4r')
    print res 
    print server.lowstate({'client':'local','tgt':'*','fun':'grains.items','token':res['token']})

