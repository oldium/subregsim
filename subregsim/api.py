'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
import logging
import random
import string
import threading

log = logging.getLogger(__name__)

class Api(object):
    def __init__(self, username, password, domains):
        self.next_id = 1
        self.username = username
        self.password = password
        self.domains = domains
        self.db = {}
        for domain in self.domains:
            self.db[domain] = []
        self.ssid = None
        self.sn = 1
        self.db_lock = threading.Lock()

    def toZone(self):
        zone = []
        zone.append("$ORIGIN .")
        zone.append("$TTL 1800")

        with self.db_lock:
            for domain in self.domains:
                zone.append("{} IN SOA ns.example.com admin.example.com ( {} 86400 900 1209600 1800 )".format(
                    domain,
                    self.sn,
                    ))

                for rr in self.db[domain]:
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
                    "count": len(self.domains),
                    "domains": [{
                        "name": domain,
                        "expire": "2023-10-20",
                        "autorenew": 0
                        } for domain in self.domains]
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

        if domain not in self.domains:
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

        if len(self.db[domain]) > 0:
            return {
                "response": {
                    "status": "ok",
                    "data": {
                        "domain": domain,
                        "records": self.db[domain]
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

        if domain not in self.domains:
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

        with self.db_lock:
            if record["type"] == "CNAME" and any(found["name"] == record["name"] and
                                                 found["type"] == record["type"] and
                                                 found["content"] == record["content"] for found in self.db[domain]):
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

                self.db[domain].append(new_record)
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

        if domain not in self.domains:
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
            found_items = [item for item in self.db[domain] if item["id"] == record["id"]]
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

        if domain not in self.domains:
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
            before_length = len(self.db[domain])
            self.db[domain] = [item for item in self.db[domain] if item["id"] != record["id"]]
            if before_length == len(self.db[domain]):
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
