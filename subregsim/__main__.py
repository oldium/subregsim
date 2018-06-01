'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)

__version__ = "0.1"

import configargparse
import logging
import signal
import threading

from .api import (Api, ApiDispatcher, ApiHttpServer)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import ssl
    has_ssl = True
except:
    has_ssl = False

def parse_command_line():
    parser = configargparse.ArgumentParser(description="Subreg.cz API simulator suitable for Python lexicon module.")
    required_group = parser.add_argument_group("required arguments")
    required_group.add_argument("--domain", required=True, env_var="SUBREGSIM_DOMAIN", help="simulated domain name")
    required_group.add_argument("--username", required=True, env_var="SUBREGSIM_USERNAME", help="expected login user name by the server")
    required_group.add_argument("--password", required=True, env_var="SUBREGSIM_PASSWORD", help="expected login password by the server")

    optional_group = parser.add_argument_group("optional arguments")
    optional_group.add_argument("-c", "--config", metavar="FILE", is_config_file=True, help="configuration file for all options (can be specified only on command-line)")
    optional_group.add_argument("--host", default="localhost", env_var="SUBREGSIM_HOST", help="server listening host name or IP address (defaults to localhost)")
    optional_group.add_argument("--port", type=int, default=80, env_var="SUBREGSIM_PORT", help="server listening port (defaults to 80)")
    optional_group.add_argument("--url", default="http://localhost:8008/", env_var="SUBREGSIM_URL", help="API root URL for WSDL generation (defaults to http://localhost:8008/)")

    if has_ssl:
        ssl_group = parser.add_argument_group("optional SSL arguments")
        ssl_group.add_argument("--ssl", dest="ssl", action="store_true", default=False, env_var="SUBREGSIM_SSL", help="enables SSL on server listening port")
        ssl_group.add_argument("--ssl-port", dest="ssl_port", type=int, default=443, metavar="PORT", env_var="SUBREGSIM_SSL_PORT", help="server SSL listening port (defaults to 443)")
        ssl_group.add_argument("--ssl-certificate", dest="ssl_certificate", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_CERTIFICATE", help="specifies server certificate")
        ssl_group.add_argument("--ssl-private-key", dest="ssl_private_key", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_PRIVATE_KEY", help="specifies server privatey key (not necessary if private key is part of certificate file)")

    parsed = parser.parse_args()

    if has_ssl and parsed.ssl and ('ssl_certificate' not in parsed or not parsed.ssl_certificate):
        parser.error("--ssl requires --ssl-certificate")

    return parsed

class TerminationHandler(object):
    def __init__(self, httpd):
        self.httpd = httpd
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

    def terminate(self, signum, frame):
        del frame   # unused

        if signum == signal.SIGTERM:
            log.info("Shutting down due to termination request")
        else:
            log.info("Shutting down due to interrupt request")
        self.httpd.shutdown()

def main():

    arguments = parse_command_line()

    api = Api(arguments.username, arguments.password, arguments.domain)
    dispatcher = ApiDispatcher(arguments.url)
    dispatcher.register_api(api)

    use_ssl = has_ssl and arguments.ssl

    httpd = ApiHttpServer((arguments.host, arguments.port), use_ssl, dispatcher)

    if use_ssl:
        log.info("Starting HTTPS server to listen on {}:{}...".format(arguments.host, arguments.ssl_port))
        httpd.socket = ssl.wrap_socket(httpd.socket,
                                       keyfile=arguments.ssl_private_key,
                                       certfile=arguments.ssl_certificate,
                                       server_side=True)
    else:
        log.info("Starting HTTP server to listen on {}:{}...".format(arguments.host, arguments.port))

    TerminationHandler(httpd)

    httpd_thread = threading.Thread(target=httpd.run, name="SOAP Server")
    httpd_thread.start()

    while httpd_thread.is_alive():
        httpd_thread.join(timeout=0.5)

if __name__ == '__main__':
    try:
        main()
    except ssl.SSLError:
        log.exception("SSL setup failed, verify that both the private key and certificate are supplied")
    except:
        log.exception("Program terminated due to exception")
