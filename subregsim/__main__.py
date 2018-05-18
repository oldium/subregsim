'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)

__version__ = "0.1"

from http.server import HTTPServer
import configargparse
import logging
import pysimplesoap.server as soapserver
import random
import signal
import string
import threading

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import ssl
    has_ssl = True
except:
    has_ssl = False

class Handler(object):
    def __init__(self, username, password, domain):
        self.next_id = 1
        self.username = username
        self.password = password
        self.domain = domain
        self.db = []
        self.ssid = None

    def login(self, login, password):
        log.info("Login: {}/{}".format(login, password))

        self.ssid = None

        if login != self.username or password != self.password:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Incorrect login or password",
                        "errorcode": {
                            "major": 500,
                            "minor": 104
                            }
                        }
                    }
                }

        self.ssid = "".join(random.SystemRandom().choice(string.digits + string.ascii_lowercase) for _ in range(32))

        return {
            "response": {
                "status": "ok",
                "data": {
                    "ssid": self.ssid
                    }
                }
            }

    def domains_list(self, ssid):
        if ssid != self.ssid:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "You are not logged",
                        "errorcode": {
                            "major": 500,
                            "minor": 101
                            }
                        }
                    }
                }

        return {
            "response": {
                "status": "ok",
                "data": {
                    "count": "1",
                    "domains": [{
                        "name": self.domain,
                        "expire": "2023-10-20",
                        "autorenew": 0
                        }]
                    }
                }
            }

    def get_dns_zone(self, ssid, domain):
        if ssid != self.ssid:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "You are not logged",
                        "errorcode": {
                            "major": 500,
                            "minor": 101
                            }
                        }
                    }
                }

        if domain != self.domain:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Invalid domain",
                        "errorcode": {
                            "major": 524,
                            "minor": 1009
                            }
                        }
                    }
                }

        if len(self.db) > 0:
            return {
                "response": {
                    "status": "ok",
                    "data": {
                        "domain": domain,
                        "records": self.db
                        }
                    }
                }
        else:
            return {
                "response": {
                    "status": "ok",
                    "data": {
                        "domain": domain
                        }
                    }
                }

    def add_dns_record(self, ssid, domain, record):
        if ssid != self.ssid:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "You are not logged",
                        "errorcode": {
                            "major": 500,
                            "minor": 101
                            }
                        }
                    }
                }

        if domain != self.domain:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Invalid domain",
                        "errorcode": {
                            "major": 524,
                            "minor": 1009
                            }
                        }
                    }
                }

        if record.get("type", None) not in ["A", "AAAA", "CNAME", "MX", "TXT", "SPF", "SRV", "NS", "TLSA", "CAA", "SSHFP"]:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Unknown record type",
                        "errorcode": {
                            "major": 524,
                            "minor": 1007
                            }
                        }
                    }
                }

        if "name" not in record:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Invalid domain name in record",
                        "errorcode": {
                            "major": 524,
                            "minor": 1006
                            }
                        }
                    }
                }

        if record["type"] == "CNAME" and any(found["name"] == record["name"] and
                                             found["type"] == record["type"] and
                                             found["content"] == record["content"] for found in self.db):
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Cannot create CNAME, where another record already exists",
                        "errorcode": {
                            "major": 524,
                            "minor": 1008
                            }
                        }
                    }
                }

        new_record = dict(record)

        new_record["id"] = self.next_id
        self.next_id += 1

        if 'ttl' not in new_record:
            new_record['ttl'] = 600
        if 'prio' not in new_record:
            new_record['prio'] = 0

        self.db.append(new_record)

        return {
            "response": {
                "status": "ok"
                }
            }

    def modify_dns_record(self, ssid, domain, record):
        if ssid != self.ssid:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "You are not logged",
                        "errorcode": {
                            "major": 500,
                            "minor": 101
                            }
                        }
                    }
                }

        if domain != self.domain:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Invalid domain",
                        "errorcode": {
                            "major": 524,
                            "minor": 1009
                            }
                        }
                    }
                }

        if "id" not in record:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Missing or empty value for record ID",
                        "errorcode": {
                            "major": 524,
                            "minor": 1002
                            }
                        }
                    }
                }

        if "type" in record and record["type"] not in ["A", "AAAA", "CNAME", "MX", "TXT", "SPF", "SRV", "NS", "TLSA", "CAA", "SSHFP"]:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Unknown record type",
                        "errorcode": {
                            "major": 524,
                            "minor": 1007
                            }
                        }
                    }
                }

        found_items = [item for item in self.db if item["id"] == record["id"]]
        if len(found_items) == 0:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Record does not exist",
                        "errorcode": {
                            "major": 524,
                            "minor": 1003
                            }
                        }
                    }
                }

        found_items[0].update(record)

        return {
            "response": {
                "status": "ok"
                }
            }

    def delete_dns_record(self, ssid, domain, record):
        if ssid != self.ssid:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "You are not logged",
                        "errorcode": {
                            "major": 500,
                            "minor": 101
                            }
                        }
                    }
                }

        if domain != self.domain:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Invalid domain",
                        "errorcode": {
                            "major": 524,
                            "minor": 1009
                            }
                        }
                    }
                }

        if "id" not in record:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Missing or empty value for record ID",
                        "errorcode": {
                            "major": 524,
                            "minor": 1002
                            }
                        }
                    }
                }

        if "type" in record and record["type"] not in ["A", "AAAA", "CNAME", "MX", "TXT", "SPF", "SRV", "NS", "TLSA", "CAA", "SSHFP"]:
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Unknown record type",
                        "errorcode": {
                            "major": 524,
                            "minor": 1007
                            }
                        }
                    }
                }

        before_length = len(self.db)
        self.db = [item for item in self.db if item["id"] != record["id"]]
        if before_length == len(self.db):
            return {
                "response": {
                    "status": "error",
                    "error": {
                        "errormsg": "Record does not exist",
                        "errorcode": {
                            "major": 524,
                            "minor": 1003
                            }
                        }
                    }
                }

        return {
            "response": {
                "status": "ok"
                }
            }

    ERROR_INFO_TYPES = {
        "errormsg": str,
        "errorcode": {
            "major": int,
            "minor": int
            }
        }

    LOGIN_REQUEST_TYPES = {
        "login": str,
        "password": str
        }

    LOGIN_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {
                "ssid": str
                },
            "error": ERROR_INFO_TYPES,
            }
        }

    GET_DNS_ZONE_REQUEST_TYPES = {
        "ssid": str,
        "domain": str
        }

    GET_DNS_ZONE_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {
                "domain": str,
                "records": [{
                    "id": int,
                    "name": str,
                    "type": str,
                    "content": str,
                    "prio": int,
                    "ttl": int
                    }]
                },
            "error": ERROR_INFO_TYPES,
            }
        }

    ADD_DNS_RECORD_REQUEST_TYPES = {
        "ssid": str,
        "domain": str,
        "record": {
            "name": str,
            "type": str,
            "content": str,
            "prio": int,
            "ttl": int
            }
        }

    ADD_DNS_RECORD_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {},
            "error": ERROR_INFO_TYPES,
            }
        }

    MODIFY_DNS_RECORD_REQUEST_TYPES = {
        "ssid": str,
        "domain": str,
        "record": {
            "id": int,
            "type": str,
            "content": str,
            "prio": int,
            "ttl": int
            }
        }

    MODIFY_DNS_RECORD_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {},
            "error": ERROR_INFO_TYPES,
            }
        }

    DELETE_DNS_RECORD_REQUEST_TYPES = {
        "ssid": str,
        "domain": str,
        "record": {
            "id": int
            }
        }

    DELETE_DNS_RECORD_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {},
            "error": ERROR_INFO_TYPES,
            }
        }

    DOMAINS_LIST_REQUEST_TYPES = {
        "ssid": str
        }

    DOMAINS_LIST_RESPONSE_TYPES = {
        "response": {
            "status": str,
            "data": {
                "count": int,
                "domains": [{
                    "name": str,
                    "expire": str,
                    "autorenew": int
                    }]
                },
            "error": ERROR_INFO_TYPES,
            }
        }

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
        if signum == signal.SIGTERM:
            log.info("Shutting down due to termination request")
        else:
            log.info("Shutting down due to interrupt request")
        self.httpd.shutdown()

class SoapHttpServer(HTTPServer):
    def __init__(self, server_address, is_ssl):
        HTTPServer.__init__(self, server_address, soapserver.SOAPHandler)
        self.is_ssl = is_ssl

    def run(self):
        try:
            self.serve_forever()
        except:
            if self.is_ssl:
                log.exception("Error running HTTPS server")
            else:
                log.exception("Error running HTTP server")
        finally:
            try:
                self.server_close()
            except:
                pass

    def handle_error(self, request, client_address):
            if self.is_ssl:
                log.exception("HTTPS request handling failed")
            else:
                log.exception("HTTP request handling failed")

class TerminateException(Exception):
    pass

def main():

    arguments = parse_command_line()

    handler = Handler(arguments.username, arguments.password, arguments.domain)

    dispatcher = soapserver.SoapDispatcher(
        name = "SubregCz",
        location = arguments.url,
        action = arguments.url,
        namespace = "http://subreg.cz/wsdl",
        prefix = "nsl",
        documentation = "Subreg.CZ domain name services",
        ns = True
        )

    dispatcher.register_function("Login", handler.login,
                             args=handler.LOGIN_REQUEST_TYPES,
                             returns=handler.LOGIN_RESPONSE_TYPES)
    dispatcher.register_function("Domains_List", handler.domains_list,
                             args=handler.DOMAINS_LIST_REQUEST_TYPES,
                             returns=handler.DOMAINS_LIST_RESPONSE_TYPES)
    dispatcher.register_function("Get_DNS_Zone", handler.get_dns_zone,
                             args=handler.GET_DNS_ZONE_REQUEST_TYPES,
                             returns=handler.GET_DNS_ZONE_RESPONSE_TYPES)
    dispatcher.register_function("Add_DNS_Record", handler.add_dns_record,
                             args=handler.ADD_DNS_RECORD_REQUEST_TYPES,
                             returns=handler.ADD_DNS_RECORD_RESPONSE_TYPES)
    dispatcher.register_function("Modify_DNS_Record", handler.modify_dns_record,
                             args=handler.MODIFY_DNS_RECORD_REQUEST_TYPES,
                             returns=handler.MODIFY_DNS_RECORD_RESPONSE_TYPES)
    dispatcher.register_function("Delete_DNS_Record", handler.delete_dns_record,
                             args=handler.DELETE_DNS_RECORD_REQUEST_TYPES,
                             returns=handler.DELETE_DNS_RECORD_RESPONSE_TYPES)

    use_ssl = has_ssl and arguments.ssl

    httpd = SoapHttpServer((arguments.host, arguments.port), use_ssl)

    if use_ssl:
        log.info("Starting HTTPS server to listen on {}:{}...".format(arguments.host, arguments.ssl_port))
        httpd.socket = ssl.wrap_socket(httpd.socket,
                                       keyfile=arguments.ssl_private_key,
                                       certfile=arguments.ssl_certificate,
                                       server_side=True)
    else:
        log.info("Starting HTTP server to listen on {}:{}...".format(arguments.host, arguments.port))

    httpd.dispatcher = dispatcher

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
