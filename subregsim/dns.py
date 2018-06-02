'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
import logging
import dnslib.server
import dnslib.zoneresolver

log = logging.getLogger(__name__)

class ApiDnsResolver(dnslib.server.BaseResolver):
    def __init__(self, api):
        dnslib.server.BaseResolver.__init__(self)
        self.api = api

    def resolve(self, request, handler):
        resolver = dnslib.zoneresolver.ZoneResolver(self.api.toZone(), True)
        return resolver.resolve(request, handler)

class ApiDns(dnslib.server.DNSServer):
    def __init__(self, resolver, address, port, tcp=False):
        dnslib.server.DNSServer.__init__(self, resolver, address, port, tcp)
