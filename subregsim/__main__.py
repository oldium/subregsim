'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)

__version__ = "0.3"

import configargparse
import logging
import signal
import threading
import time

from .api import Api
from .http.soapserver import ApiHttpServer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import ssl
    has_ssl = True
except:
    has_ssl = False

try:
    from . import dns
    has_dns = True
except:
    has_dns = False

def parse_command_line():
    parser = configargparse.ArgumentParser(description="Subreg.cz API simulator suitable for Python lexicon module.")
    required_group = parser.add_argument_group("required arguments")
    required_group.add_argument("--domain", required=True, env_var="SUBREGSIM_DOMAIN", help="simulated domain name")
    required_group.add_argument("--username", required=True, env_var="SUBREGSIM_USERNAME", help="expected login user name by the server")
    required_group.add_argument("--password", required=True, env_var="SUBREGSIM_PASSWORD", help="expected login password by the server")

    optional_group = parser.add_argument_group("optional arguments")
    optional_group.add_argument("-c", "--config", metavar="FILE", is_config_file=True, help="configuration file for all options (can be specified only on command-line)")

    web_group = parser.add_argument_group("optional server arguments")
    web_group.add_argument("--host", default="localhost", env_var="SUBREGSIM_HOST", help="server listening host name or IP address (defaults to localhost)")
    web_group.add_argument("--port", type=int, default=80, env_var="SUBREGSIM_PORT", help="server listening port (defaults to 80)")
    web_group.add_argument("--url", default="http://localhost:8008/", env_var="SUBREGSIM_URL", help="API root URL for WSDL generation (defaults to http://localhost:8008/)")

    if has_ssl:
        ssl_group = parser.add_argument_group("optional SSL arguments")
        ssl_group.add_argument("--ssl", dest="ssl", action="store_true", default=False, env_var="SUBREGSIM_SSL", help="enables SSL on server listening port")
        ssl_group.add_argument("--ssl-port", dest="ssl_port", type=int, default=443, metavar="PORT", env_var="SUBREGSIM_SSL_PORT", help="server SSL listening port (defaults to 443)")
        ssl_group.add_argument("--ssl-certificate", dest="ssl_certificate", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_CERTIFICATE", help="specifies server certificate")
        ssl_group.add_argument("--ssl-private-key", dest="ssl_private_key", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_PRIVATE_KEY", help="specifies server privatey key (not necessary if private key is part of certificate file)")

    if has_dns:
        dns_group = parser.add_argument_group("optional DNS server arguments")
        dns_group.add_argument("--dns", dest="dns", action="store_true", default=False, env_var="SUBREGSIM_DNS", help="enables DNS server")
        dns_group.add_argument("--dns-host", dest="dns_host", default="localhost", env_var="SUBREGSIM_DNS_HOST", help="DNS server listening host name or IP address (defaults to localhost)")
        dns_group.add_argument("--dns-port", dest="dns_port", type=int, default=53, metavar="PORT", env_var="SUBREGSIM_DNS_PORT", help="DNS server listening port (defaults to 53)")

    parsed = parser.parse_args()

    if has_ssl and parsed.ssl and ('ssl_certificate' not in parsed or not parsed.ssl_certificate):
        parser.error("--ssl requires --ssl-certificate")

    return parsed

terminated = False

class TerminationHandler(object):
    def __init__(self):
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

    def terminate(self, signum, frame):
        del frame   # unused

        if signum == signal.SIGTERM:
            log.info("Shutting down due to termination request")
        else:
            log.info("Shutting down due to interrupt request")

        global terminated
        terminated = True

def server_runner(server, is_ssl):
    try:
        server.serve_forever()
    except:
        if is_ssl:
            log.exception("Error running HTTPS server")
        else:
            log.exception("Error running HTTP server")
    finally:
        try:
            server.server_close()
        except:
            pass

def main():

    arguments = parse_command_line()

    use_ssl = has_ssl and arguments.ssl
    use_dns = has_dns and arguments.dns

    api = Api(arguments.username, arguments.password, arguments.domain)

    if use_ssl:
        log.info("Starting HTTPS server to listen on {}:{}...".format(arguments.host, arguments.ssl_port))

        httpd = ApiHttpServer((arguments.host, arguments.ssl_port), arguments.url, api, use_ssl)
        httpd.socket = ssl.wrap_socket(httpd.socket,
                                       keyfile=arguments.ssl_private_key,
                                       certfile=arguments.ssl_certificate,
                                       server_side=True)
    else:
        log.info("Starting HTTP server to listen on {}:{}...".format(arguments.host, arguments.port))
        httpd = ApiHttpServer((arguments.host, arguments.port), arguments.url, api, use_ssl)

    stop_servers = [httpd]

    if use_dns:
        log.info("Starting DNS server to listen on {}:{}...".format(arguments.dns_host, arguments.dns_port))
        api_resolver = dns.ApiDnsResolver(api)
        dns_udp = dns.ApiDns(api_resolver, arguments.dns_host, arguments.dns_port, False)
        dns_tcp = dns.ApiDns(api_resolver, arguments.dns_host, arguments.dns_port, True)

        stop_servers.append(dns_udp)
        stop_servers.append(dns_tcp)

        dns_udp.start_thread()
        dns_tcp.start_thread()

    TerminationHandler()

    httpd_thread = threading.Thread(target=server_runner, args=(httpd, use_ssl), name="SOAP Server")
    httpd_thread.start()

    while not terminated:
        time.sleep(0.5)

    httpd.shutdown()
    httpd_thread.join()

    if use_dns:
        dns_udp.stop()
        dns_tcp.stop()

        dns_udp.thread.join()
        dns_tcp.thread.join()

if __name__ == '__main__':
    try:
        main()
    except ssl.SSLError:
        log.exception("SSL setup failed, verify that both the private key and certificate are supplied")
    except:
        log.exception("Program terminated due to exception")
