from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import socket

class MyHandler(SimpleHTTPRequestHandler):
    pass

class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6

server_ipv4 = HTTPServer(('', 8080), MyHandler)
server_ipv6 = HTTPServerV6(('::1', 8080), MyHandler)

th4 = Thread(target=server_ipv4.serve_forever)
th6 = Thread(target=server_ipv6.serve_forever)

th4.start()
th6.start()
