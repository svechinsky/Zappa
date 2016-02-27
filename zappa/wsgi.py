import logging

from urllib import urlencode
from requestlogger import ApacheFormatter
from StringIO import StringIO

def create_wsgi_request(event_info, server_name='zappa', script_name=None,
                        trailing_slash=True):
        """
        Given some event_info,
        create and return a valid WSGI request environ.
        """

        method = event_info['method']
        body = str(event_info['body'])
        params = event_info['params']
        query = event_info['query']
        headers = event_info['headers']

        path = "/"
        for key in sorted(params.keys()):
            path = path + params[key] + "/"

        # This determines if we should return
        # site.com/resource/ : site.com/resource
        # site.com/resource : site.com/resource
        # vs.
        # site.com/resource/ : site.com/resource/
        # site.com/resource : site.com/resource/
        # If no params are present, keep the slash.
        if not trailing_slash and params.keys():
            path = path[:-1]

        query_string = urlencode(query)

        x_forwarded_for = headers.get('X-Forwarded-For', '')
        if ',' in x_forwarded_for:
            remote_addr = x_forwarded_for.split(', ')[0]
        else:
            remote_addr = '127.0.0.1'

        environ = {
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'REMOTE_ADDR': remote_addr,
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': str(''),
            'SERVER_NAME': str(server_name),
            'SERVER_PORT': str('80'),
            'SERVER_PROTOCOL': str('HTTP/1.1'),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': str('http'),
            'wsgi.input': body,
            'wsgi.errors': str(''),
            'wsgi.multiprocess': False,
            'wsgi.multithread': False,
            'wsgi.run_once': False,
        }

        # Input processing
        if method == "POST":
            environ['wsgi.input'] = StringIO(body)
            if event_info["headers"].has_key('Content-Type'):
                environ['CONTENT_TYPE'] = event_info["headers"]['Content-Type']
            environ['CONTENT_LENGTH'] = str(len(body))

        for header in event_info["headers"]:
            wsgi_name = "HTTP_" + header.upper().replace('-', '_')
            environ[wsgi_name] = str(event_info["headers"][header])

        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if script_name in path_info:
                environ['PATH_INFO'].replace(script_name, '')

        return environ

def common_log(environ, response, response_time=None):
    """
    Given the WSGI environ and the response,
    log this event in Common Log Format.

    """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if response_time:
        formatter = ApacheFormatter(with_response_time=True)
        log_entry = formatter(response.status_code, environ, len(response.content), rt_ms=response_time)
    else:
        formatter = ApacheFormatter(with_response_time=False)
        log_entry = formatter(response.status_code, environ, len(response.content))
    
    logger.info(log_entry)

    return log_entry
