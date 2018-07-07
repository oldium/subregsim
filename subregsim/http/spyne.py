'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
import logging

from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode
from spyne.model.complex import ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

log = logging.getLogger(__name__)

# `True` means more precise simulation of Subreg.cz API (WSDL presentation),
# but does not work at the moment... See https://github.com/arskom/spyne/issues/571
USE_PORT_TYPE = False

class Error_Code(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('major', Integer),
        ('minor', Integer)
        ]

class Error_Info(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('errormsg', Unicode),
        ('errorcode', Error_Code)
        ]

class Login_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    ssid = Unicode

class Login_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Login_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Login_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Login_Response

class Get_DNS_Zone_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('id', Integer),
        ('name', Unicode),
        ('type', Unicode),
        ('content', Unicode.customize(min_occurs=0)),
        ('prio', Integer.customize(min_occurs=0)),
        ('ttl', Integer.customize(min_occurs=0)),
        ]

class Get_DNS_Zone_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('domain', Unicode),
        ('records', Get_DNS_Zone_Record.customize(min_occurs=0, max_occurs='unbounded'))
        ]

class Get_DNS_Zone_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Get_DNS_Zone_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Get_DNS_Zone_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Get_DNS_Zone_Response

class Add_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('name', Unicode),
        ('type', Unicode),
        ('content', Unicode.customize(min_occurs=0)),
        ('prio', Integer.customize(min_occurs=0)),
        ('ttl', Integer.customize(min_occurs=0)),
        ]

class Add_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    pass

class Add_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Add_DNS_Record_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Add_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Add_DNS_Record_Response

class Modify_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('id', Integer),
        ('type', Unicode),
        ('content', Unicode.customize(min_occurs=0)),
        ('prio', Integer.customize(min_occurs=0)),
        ('ttl', Integer.customize(min_occurs=0)),
        ]

class Modify_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    pass

class Modify_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Modify_DNS_Record_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Modify_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Modify_DNS_Record_Response

class Delete_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    id = Integer

class Delete_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    pass

class Delete_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Delete_DNS_Record_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Delete_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Delete_DNS_Record_Response

class Domains_List_Domain(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('name', Unicode),
        ('expire', Unicode),
        ('autorenew', Integer)
        ]

class Domains_List_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('count', Integer),
        ('domains', Domains_List_Domain.customize(min_occurs=0, max_occurs='unbounded'))
        ]

class Domains_List_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    _type_info = [
        ('status', Unicode),
        ('data', Domains_List_Data.customize(min_occurs=0)),
        ('error', Error_Info.customize(min_occurs=0))
        ]

class Domains_List_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/wsdl"
    response = Domains_List_Response

class SubregCzService(ServiceBase):
    __port_types__ = ("SubregCz",) if USE_PORT_TYPE else ()

    @rpc(Unicode, Unicode, _returns=Login_Container, _body_style='out_bare', _operation_name="Login",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def login(ctx, login, password):
        return ctx.app.config["api"].login(login, password)

    @rpc(Unicode, _returns=Domains_List_Container, _operation_name="Domains_List",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def domains_list(ctx, ssid):
        return ctx.app.config["api"].domains_list(ssid)

    @rpc(Unicode, Unicode, _returns=Get_DNS_Zone_Container, _operation_name="Get_DNS_Zone",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def get_dns_zone(ctx, ssid, domain):
        return ctx.app.config["api"].get_dns_zone(ssid, domain)

    @rpc(Unicode, Unicode, Add_DNS_Record_Record, _returns=Add_DNS_Record_Container, _operation_name="Add_DNS_Record",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def add_dns_record(ctx, ssid, domain, record):
        return ctx.app.config["api"].add_dns_record(ssid, domain, record.as_dict())

    @rpc(Unicode, Unicode, Modify_DNS_Record_Record, _returns=Modify_DNS_Record_Container, _operation_name="Modify_DNS_Record",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def modify_dns_record(ctx, ssid, domain, record):
        return ctx.app.config["api"].modify_dns_record(ssid, domain, record.as_dict())

    @rpc(Unicode, Unicode, Delete_DNS_Record_Record, _returns=Delete_DNS_Record_Container, _operation_name="Delete_DNS_Record",
         _soap_port_type="SubregCz" if USE_PORT_TYPE else None
         )
    def delete_dns_record(ctx, ssid, domain, record):
        return ctx.app.config["api"].delete_dns_record(ssid, domain, record.as_dict())

class ApiHandler(WSGIRequestHandler):
    def do_POST(self):
        WSGIRequestHandler.do_POST(self)

    def do_GET(self):
        if self.path == "/wsdl":
            self.path = "/"
        WSGIRequestHandler.do_GET(self)

class ApiApplication(WsgiApplication):
    def is_wsdl_request(self, req_env):
        # Check the wsdl for the service.
        return (
            req_env['REQUEST_METHOD'].upper() == 'GET'
            and req_env['PATH_INFO'] == '/wsdl'
            )

class ApiHttpServer(WSGIServer):
    def __init__(self, server_address, url, api, is_ssl):
        WSGIServer.__init__(self, server_address, ApiHandler)
        self.is_ssl = is_ssl

        if self.is_ssl:
            self.base_environ["HTTPS"] = "yes"

        app = ApiApplication(Application([SubregCzService], 'http://subreg.cz/wsdl',
                                         'SubregCzService',
                                         in_protocol=Soap11(),
                                         out_protocol=Soap11(),
                                         config={"api":api}))

        self.set_app(app)

        app.doc.wsdl11.build_interface_document(url)

    def handle_error(self, request, client_address):
        del request         # unused

        if self.is_ssl:
            log.exception("HTTPS request handling from {} failed".format(client_address[0]))
        else:
            log.exception("HTTP request handling from {} failed".format(client_address[0]))
