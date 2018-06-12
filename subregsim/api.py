'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
import logging
import random
import string
import threading
import pysimplesoap.server as soapserver
from http.server import HTTPServer

log = logging.getLogger(__name__)

class Api(object):
    def __init__(self, username, password, domain):
        self.next_id = 1
        self.username = username
        self.password = password
        self.domain = domain
        self.db = []
        self.ssid = None
        self.sn = 1
        self.db_lock = threading.Lock()

    def toZone(self):
        zone = []
        zone.append("$ORIGIN .")
        zone.append("$TTL 1800")

        with self.db_lock:
            zone.append("{} IN SOA ns.example.com admin.example.com ( {} 86400 900 1209600 1800 )".format(
                self.domain,
                self.sn,
                ))

            for rr in self.db:
                name = rr["name"]
                type = rr["type"]
                content = rr["content"] if "content" in rr else ""
                prio = rr["prio"]
                ttl = rr["ttl"] if rr["ttl"] != 1800 else ""

                if type != "MX":
                    prio = ""

                if type == "TXT":
                    content = '"{}"'.format(content.replace('"', r'\"'))

                zone.append("{} {} IN {} {} {}".format(
                    name, ttl, type, prio, content))

        return "\n".join(zone)

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

        with self.db_lock:
            self.db.append(new_record)
            self.sn += 1

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

        with self.db_lock:
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
            self.sn += 1

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

        with self.db_lock:
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

            self.sn += 1

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
                               args=api.LOGIN_REQUEST_TYPES,
                               returns=api.LOGIN_RESPONSE_TYPES)
        self.register_function("Domains_List", api.domains_list,
                               args=api.DOMAINS_LIST_REQUEST_TYPES,
                               returns=api.DOMAINS_LIST_RESPONSE_TYPES)
        self.register_function("Get_DNS_Zone", api.get_dns_zone,
                               args=api.GET_DNS_ZONE_REQUEST_TYPES,
                               returns=api.GET_DNS_ZONE_RESPONSE_TYPES)
        self.register_function("Add_DNS_Record", api.add_dns_record,
                               args=api.ADD_DNS_RECORD_REQUEST_TYPES,
                               returns=api.ADD_DNS_RECORD_RESPONSE_TYPES)
        self.register_function("Modify_DNS_Record", api.modify_dns_record,
                               args=api.MODIFY_DNS_RECORD_REQUEST_TYPES,
                               returns=api.MODIFY_DNS_RECORD_RESPONSE_TYPES)
        self.register_function("Delete_DNS_Record", api.delete_dns_record,
                               args=api.DELETE_DNS_RECORD_REQUEST_TYPES,
                               returns=api.DELETE_DNS_RECORD_RESPONSE_TYPES)

class ApiHandler(soapserver.SOAPHandler):
    def do_GET(self):
        if self.path == "/wsdl":
            self.path = "/"
        soapserver.SOAPHandler.do_GET(self)

class ApiHttpServer(HTTPServer):
    def __init__(self, server_address, is_ssl, dispatcher):
        HTTPServer.__init__(self, server_address, ApiHandler)
        self.is_ssl = is_ssl
        self.dispatcher = dispatcher

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
        del request         # unused

        if self.is_ssl:
            log.exception("HTTPS request handling from {} failed".format(client_address[0]))
        else:
            log.exception("HTTP request handling from {} failed".format(client_address[0]))
