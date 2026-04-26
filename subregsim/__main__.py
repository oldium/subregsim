'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)

__version__ = "0.5.1"

import configargparse
import logging
import ssl

from .api import Api
from . import dns
from .subreg import ApiHttpServer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def parse_command_line():
    parser = configargparse.ArgumentParser(description="Subreg.cz API simulator suitable for Python lexicon module.")
    optional_group = parser.add_argument_group("optional arguments")
    optional_group.add_argument("-c", "--config", metavar="FILE", is_config_file=True, help="configuration file for all options (can be specified only on command-line)")
    optional_group.add_argument("--domain", dest="domains", action="append", env_var="SUBREGSIM_DOMAIN", default=["example.com"], help="simulated domain name (defaults to example.com); may be repeated on the command-line, or given as a list (e.g. [example.com, example.net]) in the config file or SUBREGSIM_DOMAIN env var")
    optional_group.add_argument("--username", env_var="SUBREGSIM_USERNAME", default="username", help="expected login user name by the server (defaults to username)")
    optional_group.add_argument("--password", env_var="SUBREGSIM_PASSWORD", default="password", help="expected login password by the server (defaults to password)")

    web_group = parser.add_argument_group("optional server arguments")
    web_group.add_argument("--host", default="localhost", env_var="SUBREGSIM_HOST", help="server listening host name or IP address (defaults to localhost)")
    web_group.add_argument("--port", type=int, default=80, env_var="SUBREGSIM_PORT", help="server listening port (defaults to 80)")
    web_group.add_argument("--url", default="http://localhost:8008/", env_var="SUBREGSIM_URL", help="API root URL for WSDL generation (defaults to http://localhost:8008/)")

    ssl_group = parser.add_argument_group("optional SSL arguments")
    ssl_group.add_argument("--ssl", dest="ssl", action="store_true", default=False, env_var="SUBREGSIM_SSL", help="enables SSL on server listening port")
    ssl_group.add_argument("--ssl-port", dest="ssl_port", type=int, default=443, metavar="PORT", env_var="SUBREGSIM_SSL_PORT", help="server SSL listening port (defaults to 443)")
    ssl_group.add_argument("--ssl-certificate", dest="ssl_certificate", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_CERTIFICATE", help="specifies server certificate")
    ssl_group.add_argument("--ssl-private-key", dest="ssl_private_key", metavar="PEM-FILE", default=None, env_var="SUBREGSIM_SSL_PRIVATE_KEY", help="specifies server privatey key (not necessary if private key is part of certificate file)")

    dns_group = parser.add_argument_group("optional DNS server arguments")
    dns_group.add_argument("--dns", dest="dns", action="store_true", default=False, env_var="SUBREGSIM_DNS", help="enables DNS server")
    dns_group.add_argument("--dns-host", dest="dns_host", default="localhost", env_var="SUBREGSIM_DNS_HOST", help="DNS server listening host name or IP address (defaults to localhost)")
    dns_group.add_argument("--dns-port", dest="dns_port", type=int, default=53, metavar="PORT", env_var="SUBREGSIM_DNS_PORT", help="DNS server listening port (defaults to 53)")

    parsed = parser.parse_args()

    if parsed.ssl and ('ssl_certificate' not in parsed or not parsed.ssl_certificate):
        parser.error("--ssl requires --ssl-certificate")

    return parsed

def main():

    arguments = parse_command_line()

    api = Api(arguments.username, arguments.password, arguments.domains)

    if arguments.ssl:
        log.info("Starting HTTPS server to listen on {}:{}...".format(arguments.host, arguments.ssl_port))

        httpd = ApiHttpServer((arguments.host, arguments.ssl_port), arguments.url, api, arguments.ssl)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(arguments.ssl_certificate, arguments.ssl_private_key)
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
    else:
        log.info("Starting HTTP server to listen on {}:{}...".format(arguments.host, arguments.port))
        httpd = ApiHttpServer((arguments.host, arguments.port), arguments.url, api, arguments.ssl)

    if arguments.dns:
        log.info("Starting DNS server to listen on {}:{}...".format(arguments.dns_host, arguments.dns_port))
        api_resolver = dns.ApiDnsResolver(api)
        dns_udp = dns.ApiDns(api_resolver, arguments.dns_host, arguments.dns_port, False)
        dns_tcp = dns.ApiDns(api_resolver, arguments.dns_host, arguments.dns_port, True)

        dns_udp.start_thread()
        dns_tcp.start_thread()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Terminating...")
    except Exception as e:
        log.exception(f"Error running HTTP{'S' if arguments.ssl else ''} server", e)
    finally:
        try:
            httpd.server_close()
        except:
            pass

        if arguments.dns:
            dns_udp.stop()
            dns_tcp.stop()

            dns_udp.thread.join()
            dns_tcp.thread.join()

def run():
    try:
        main()
    except ssl.SSLError as e:
        log.exception("SSL setup failed, verify that both the private key and certificate are supplied", e)
    except Exception as e:
        log.exception("Program terminated due to exception", e)

if __name__ == '__main__':
    run()
