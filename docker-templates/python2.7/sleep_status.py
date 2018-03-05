#!/usr/bin/env python
import BaseHTTPServer
import SocketServer
import argparse
import datetime

def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('status_port',type=int,help='Port to return the service status, in HTTP')
    parser.add_argument('sleep',type=int,help='Time to sleep before returning healthy')
    if args is None:
        return parser.parse_args()
    else:
        return parser.parse_args(args=args)

def class_bind_obj(**kwargs):
    def decorator(Clz):
        class NewCls(Clz):
            pass

        NewCls.__dict__.update(kwargs)
        return NewCls
    return decorator

class ThreadingHTTPServer (SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def handle_error(self, request, client_address):
        import sys
        etype, evalue, _ = sys.exc_info()
        print ('{1}:"{2}" processing request from {0}'.format(client_address, etype, evalue))

class NameSpace(object):
    pass

class HealthCheckHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_request (self, code=None, size=None):
        if str(code)[0] in '23':
            return
        else:
            return BaseHTTPServer.BaseHTTPRequestHandler.log_request(self, code=code, size=size)

    def do_GET(self):
        return_msg = ''

        start_elapsed= datetime.datetime.utcnow() - self.repl_status.started
        if start_elapsed < datetime.timedelta(0, self.SLEEP):
            return_msg += 'Started {0} seconds, not yet healthy'.format(start_elapsed)
            self.log_message(return_msg)
            self.send_response(500)
        else:
            self.send_response(200)

        self.end_headers()
        self.wfile.write(return_msg)

def start_check_srv(status_port, sleep_time):
    req_handler = class_bind_obj(TIMEOUT=5, SLEEP=sleep_time, repl_status=NameSpace())(HealthCheckHTTPRequestHandler)
    setattr(req_handler.repl_status, 'started', datetime.datetime.utcnow())
    listen_addr=('', status_port)
    httpd = ThreadingHTTPServer(listen_addr, req_handler) 
    print ("Serving tcp status on {status_port}".format(status_port=listen_addr))
    httpd.allow_reuse_address = True
    try:
        httpd.serve_forever()
    finally:
        httpd.shutdown()
        httpd.server_close()

def main():
    args = parse_args()
    start_check_srv(args.status_port, args.sleep)
    
if __name__ == '__main__':
    main()
