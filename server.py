from argparse import ArgumentParser
from hashlib import md5
from http.server import HTTPServer, SimpleHTTPRequestHandler
from logging import getLogger, Formatter, INFO
from logging.handlers import RotatingFileHandler
from urllib.parse import unquote
from os import curdir, pardir, fstat
from os.path import dirname, join, exists, getmtime, isdir
from posixpath import normpath
from time import localtime, strftime, sleep

logger = None

def setup_server_log():
    global logger

    logger = getLogger("httpd")
    formatter = Formatter('%(message)s')
    fh = RotatingFileHandler("{}".format(ARGS.log_path))
    fh.backupCount = 20
    fh.setFormatter(formatter)
    fh.setLevel(INFO)
    logger.addHandler(fh)
    logger.setLevel(INFO)


class MyHandler(SimpleHTTPRequestHandler):
    address_family = socket.AF_INET6
    def __init__(self, *args):
        """
        Inicializa classe criando instancia do handler.

        os valores passados por parâmetro e envia *args para
            init padrão da superclasse
        """
        SimpleHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        """
        Cuida do retorno da ETAG.

        Vars:
            - path: Faz um match no path do server
            - md5_key: Hash do arquivo qual foi feita a requisição

        Args:
            - handler: handler do server que vai executar as funções da etag
        """
        sleep(int(ARGS.get_delay))
        path = self.translate_path(self.path)
        md5_key = None
        if exists(path) and not isdir(path):
            with open(path, 'rb') as f:
                # Gera o MD5 do arquivo no diretório
                st = fstat(f.fileno())
                length = st.st_size
                data = f.read()
                _md5 = md5()
                _md5.update(data)
                md5_key = _md5.hexdigest()

        if md5_key:
            if self.headers['If-None-Match'] == md5_key:
                self.send_response(304)
                self.send_header('ETag', '{}'.format(_md5.hexdigest()))
                self.send_header('Keep-Alive', 'timeout=5, max=100')
                self.end_headers()

            else:
                self.send_response(200)
                self.send_header('Content-type', "text/html")
                self.send_header('Content-Length', length)
                self.send_header('ETag', '{}'.format(_md5.hexdigest()))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Last-Modified',
                                 strftime("%a %d %b %Y %H:%M:%S GMT ----",
                                          localtime(getmtime(path))))
                self.end_headers()
                self.wfile.write(data)
                f.close()

        if isdir(path):
            self.send_response(200)
            self.wfile.write(b"Use: localhost:port/file")

    def do_POST(self):
        u"""Retorna o arquivo específico."""
        sleep(int(ARGS.post_delay))
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        logger.info("POST: {}".format(post_data.decode()))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, string, *args):
        """loga as mensagens no log do servidor."""
        logger.info("%s - - [%s] %s" %
                    (self.address_string(),
                     self.log_date_time_string(),
                     string % args))

    def translate_path(self, path):
        """Transcreve path para uma diretório fixo."""
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        try:
            path = unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            path = unquote(path)
        path = normpath(path)
        words = path.split('/')
        words = filter(None, words)

        path = ARGS.path

        for word in words:
            if dirname(word) or word in (curdir, pardir):
                continue
            path = join(path, word)
        if trailing_slash:
            path += '/'

        return path


parser = ArgumentParser()
parser.add_argument('--port', default=8000,
                    help='Porta do servidor')

parser.add_argument('--path', default='.',
                    help='Caminho disponibilizado pelo server')

parser.add_argument('--log_path', default='log.log',
                    help='arquivo de log do servidor')

parser.add_argument(
    '--get_delay',
    default=0,
    help='delay de resposta do servidor em requisições do tipo GET')

parser.add_argument(
    '--post_delay',
    default=0,
    help='delay de resposta do servidor em requisições do tipo POST')

parser.add_argument(
    '--ipv6',
    default=False,
    help='bool')

parser.add_argument(
    '--ipv6_port',
    default=8081,
    help='porta do servidor ipv6')

ARGS = parser.parse_args()

setup_server_log()
server = HTTPServer(('', int(ARGS.port)), MyHandler)

if ARGS.ipv6:
    server6 = HTTPServer(('::1', int(ARGS.ipv6_port)), MyHandler)
    server6.serve_forever()

server.serve_forever()
