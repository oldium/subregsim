'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
import logging

import pysimplesoap.server as soapserver
from http.server import HTTPServer

log = logging.getLogger(__name__)

class SoapTypes(object):
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

class ApiDispatcher(soapserver.SoapDispatcher):
    def __init__(self, url):
        soapserver.SoapDispatcher.__init__(
            self,
            name = "SubregCz",
            location = url,
            action = url,
            namespace = "http://subreg.cz/wsdl",
            prefix = "nsl",
            documentation = "Subreg.CZ domain name services",
            ns = True
            )

    def register_api(self, api):
        self.register_function("Login", api.login,
                               args=SoapTypes.LOGIN_REQUEST_TYPES,
                               returns=SoapTypes.LOGIN_RESPONSE_TYPES)
        self.register_function("Domains_List", api.domains_list,
                               args=SoapTypes.DOMAINS_LIST_REQUEST_TYPES,
                               returns=SoapTypes.DOMAINS_LIST_RESPONSE_TYPES)
        self.register_function("Get_DNS_Zone", api.get_dns_zone,
                               args=SoapTypes.GET_DNS_ZONE_REQUEST_TYPES,
                               returns=SoapTypes.GET_DNS_ZONE_RESPONSE_TYPES)
        self.register_function("Add_DNS_Record", api.add_dns_record,
                               args=SoapTypes.ADD_DNS_RECORD_REQUEST_TYPES,
                               returns=SoapTypes.ADD_DNS_RECORD_RESPONSE_TYPES)
        self.register_function("Modify_DNS_Record", api.modify_dns_record,
                               args=SoapTypes.MODIFY_DNS_RECORD_REQUEST_TYPES,
                               returns=SoapTypes.MODIFY_DNS_RECORD_RESPONSE_TYPES)
        self.register_function("Delete_DNS_Record", api.delete_dns_record,
                               args=SoapTypes.DELETE_DNS_RECORD_REQUEST_TYPES,
                               returns=SoapTypes.DELETE_DNS_RECORD_RESPONSE_TYPES)

class ApiHandler(soapserver.SOAPHandler):
    def do_GET(self):
        if self.path == "/wsdl":
            self.path = "/"
        soapserver.SOAPHandler.do_GET(self)

class ApiHttpServer(HTTPServer):
    def __init__(self, server_address, url, api, is_ssl):
        HTTPServer.__init__(self, server_address, ApiHandler)
        self.is_ssl = is_ssl

        self.dispatcher = ApiDispatcher(url)
        self.dispatcher.register_api(api)

    def handle_error(self, request, client_address):
        del request         # unused

        if self.is_ssl:
            log.exception("HTTPS request handling from {} failed".format(client_address[0]))
        else:
            log.exception("HTTP request handling from {} failed".format(client_address[0]))
