'''
Subreg.cz API simulator suitable for Python lexicon module.
'''

from __future__ import (absolute_import, print_function)
from email.message import Message
import importlib.util
import logging
import pathlib
import re
import sys
import warnings
from importlib import metadata


if sys.version_info >= (3, 13):
    import collections
    import types
    from collections import abc

    # Spyne 2.14 still expects stdlib aliases and helper modules removed in
    # newer Python releases, so patch them for Python 3.13+ runtimes.
    if sys.version_info[:2] <= (3, 14):
        original_showwarning = warnings.showwarning


        def showwarning(message, category, filename, lineno, file=None, line=None):
            if (
                category is SyntaxWarning
                and "invalid escape sequence" in str(message)
                and re.search(r"spyne[\\/]+protocol[\\/]http\.py$", filename)
            ):
                return
            return original_showwarning(message, category, filename, lineno, file=file, line=line)


        warnings.showwarning = showwarning

    def parse_header(value):
        message = Message()
        message["content-type"] = value
        return message.get_content_type(), dict(message.get_params()[1:])


    collections.Iterable = abc.Iterable
    collections.Mapping = abc.Mapping
    collections.MutableMapping = abc.MutableMapping
    collections.MutableSet = abc.MutableSet
    cgi_module = types.ModuleType("cgi")
    cgi_module.parse_header = parse_header
    sys.modules.setdefault("cgi", cgi_module)

    if "spyne.util.six" not in sys.modules:
        # Resolve the installed Spyne package location from distribution
        # metadata so this works in both local uv environments and containers.
        spyne_dist = metadata.distribution("spyne")
        spyne_six_path = pathlib.Path(spyne_dist.locate_file("spyne/util/six.py"))
        spec = importlib.util.spec_from_file_location("spyne.util.six", spyne_six_path)
        spyne_six = importlib.util.module_from_spec(spec)
        sys.modules["spyne.util.six"] = spyne_six
        spec.loader.exec_module(spyne_six)
    else:
        spyne_six = sys.modules["spyne.util.six"]

    spyne_six._importer.load_module("spyne.util.six.moves")
    spyne_six._importer.load_module("spyne.util.six.moves.collections_abc")
    spyne_six._importer.load_module("spyne.util.six.moves.http_cookies")
    spyne_six._importer.load_module("spyne.util.six.moves.urllib")
    spyne_six._importer.load_module("spyne.util.six.moves.urllib.parse")

from socketserver import ThreadingMixIn
from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode
from spyne.model.complex import ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

log = logging.getLogger(__name__)

RequiredInteger = Integer.customize(nillable=False, min_occurs=1)
RequiredUnicode = Unicode.customize(nillable=False, min_occurs=1)
OptionalInteger = Integer.customize(nillable=False, min_occurs=0)
OptionalUnicode = Unicode.customize(nillable=False, min_occurs=0)

class Error_Code(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('major', RequiredInteger),
        ('minor', RequiredInteger)
        ]

class Error_Info(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('errormsg', RequiredUnicode),
        ('errorcode', Error_Code.customize(nillable=False, min_occurs=1))
        ]

class Login_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    ssid = RequiredUnicode

class Login_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Login_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Login_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Login_Response.customize(nillable=False, min_occurs=1)

class Get_DNS_Zone_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('id', RequiredInteger),
        ('name', RequiredUnicode),
        ('type', RequiredUnicode),
        ('content', OptionalUnicode),
        ('prio', OptionalInteger),
        ('ttl', OptionalInteger),
        ]

class Get_DNS_Zone_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('domain', RequiredUnicode),
        ('records', Get_DNS_Zone_Record.customize(nillable=False, min_occurs=0, max_occurs='unbounded'))
        ]

class Get_DNS_Zone_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Get_DNS_Zone_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Get_DNS_Zone_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Get_DNS_Zone_Response.customize(nillable=False, min_occurs=1)

class Add_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('name', RequiredUnicode),
        ('type', RequiredUnicode),
        ('content', OptionalUnicode),
        ('prio', OptionalInteger),
        ('ttl', OptionalInteger),
        ]

class Add_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    pass

class Add_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Add_DNS_Record_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Add_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Add_DNS_Record_Response.customize(nillable=False, min_occurs=1)

class Modify_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('id', RequiredInteger),
        ('type', RequiredUnicode),
        ('content', OptionalUnicode),
        ('prio', OptionalInteger),
        ('ttl', OptionalInteger),
        ]

class Modify_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    pass

class Modify_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Modify_DNS_Record_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Modify_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Modify_DNS_Record_Response.customize(nillable=False, min_occurs=1)

class Delete_DNS_Record_Record(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    id = RequiredInteger

class Delete_DNS_Record_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    pass

class Delete_DNS_Record_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Delete_DNS_Record_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Delete_DNS_Record_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Delete_DNS_Record_Response.customize(nillable=False, min_occurs=1)

class Domains_List_Domain(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('name', RequiredUnicode),
        ('expire', RequiredUnicode),
        ('autorenew', RequiredInteger)
        ]

class Domains_List_Data(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('count', RequiredInteger),
        ('domains', Domains_List_Domain.customize(nillable=False, min_occurs=0, max_occurs='unbounded'))
        ]

class Domains_List_Response(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    _type_info = [
        ('status', RequiredUnicode),
        ('data', Domains_List_Data.customize(nillable=False, min_occurs=0)),
        ('error', Error_Info.customize(nillable=False, min_occurs=0))
        ]

class Domains_List_Container(ComplexModel):
    __namespace__ = "http://subreg.cz/types"
    response = Domains_List_Response.customize(nillable=False, min_occurs=1)

class SubregCzService(ServiceBase):
    __port_types__ = ("SubregCz",)

    # Method names use the real subreg.cz operation casing (Login, Get_DNS_Zone…)
    # so that spyne picks them up as the wsdl:operation name. _in_message_name /
    # _out_message_name carry an explicit namespace so the request/response body
    # elements live in http://subreg.cz/types while the wsdl-level service,
    # portType, binding, and message definitions stay under the Application's
    # tns http://subreg.cz/wsdl, matching the real subreg.cz WSDL.
    @rpc(RequiredUnicode, RequiredUnicode, _returns=Login_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Login",
         _out_message_name="{http://subreg.cz/types}Login_Container",
         _port_type="SubregCz"
         )
    def Login(ctx, login, password):
        return ctx.app.config["api"].login(login, password)

    @rpc(RequiredUnicode, _returns=Domains_List_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Domains_List",
         _out_message_name="{http://subreg.cz/types}Domains_List_Container",
         _port_type="SubregCz"
         )
    def Domains_List(ctx, ssid):
        return ctx.app.config["api"].domains_list(ssid)

    @rpc(RequiredUnicode, RequiredUnicode, _returns=Get_DNS_Zone_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Get_DNS_Zone",
         _out_message_name="{http://subreg.cz/types}Get_DNS_Zone_Container",
         _port_type="SubregCz"
         )
    def Get_DNS_Zone(ctx, ssid, domain):
        return ctx.app.config["api"].get_dns_zone(ssid, domain)

    @rpc(RequiredUnicode, RequiredUnicode, Add_DNS_Record_Record.customize(nillable=False, min_occurs=1),
         _returns=Add_DNS_Record_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Add_DNS_Record",
         _out_message_name="{http://subreg.cz/types}Add_DNS_Record_Container",
         _port_type="SubregCz"
         )
    def Add_DNS_Record(ctx, ssid, domain, record):
        return ctx.app.config["api"].add_dns_record(ssid, domain, record.as_dict())

    @rpc(RequiredUnicode, RequiredUnicode, Modify_DNS_Record_Record.customize(nillable=False, min_occurs=1),
         _returns=Modify_DNS_Record_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Modify_DNS_Record",
         _out_message_name="{http://subreg.cz/types}Modify_DNS_Record_Container",
         _port_type="SubregCz"
         )
    def Modify_DNS_Record(ctx, ssid, domain, record):
        return ctx.app.config["api"].modify_dns_record(ssid, domain, record.as_dict())

    @rpc(RequiredUnicode, RequiredUnicode, Delete_DNS_Record_Record.customize(nillable=False, min_occurs=1),
         _returns=Delete_DNS_Record_Container,
         _body_style='out_bare',
         _in_message_name="{http://subreg.cz/types}Delete_DNS_Record",
         _out_message_name="{http://subreg.cz/types}Delete_DNS_Record_Container",
         _port_type="SubregCz"
         )
    def Delete_DNS_Record(ctx, ssid, domain, record):
        return ctx.app.config["api"].delete_dns_record(ssid, domain, record.as_dict())

class ApiApplication(WsgiApplication):
    def __init__(self, app, service_url):
        super().__init__(app)
        self.service_url = service_url

    def is_wsdl_request(self, req_env):
        # Check the wsdl for the service.
        return (
            req_env['REQUEST_METHOD'].upper() == 'GET'
            and req_env['PATH_INFO'] == '/wsdl'
            )

    def handle_wsdl_request(self, req_env, start_response, url):
        return super().handle_wsdl_request(req_env, start_response, self.service_url)

class ApiHttpServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

    def __init__(self, server_address, url, api, is_ssl):
        WSGIServer.__init__(self, server_address, WSGIRequestHandler)
        self.is_ssl = is_ssl

        if self.is_ssl:
            self.base_environ["HTTPS"] = "yes"

        spyne_app = Application([SubregCzService], 'http://subreg.cz/wsdl',
                                'SubregCzService',
                                in_protocol=Soap11(),
                                out_protocol=Soap11(),
                                config={"api":api})

        # Spyne keys service_method_map by {Application.tns}method.name, so it
        # only matches incoming requests whose body element lives in the same
        # namespace as the WSDL service. The real subreg.cz WSDL splits the
        # namespaces (service in http://subreg.cz/wsdl, request elements in
        # http://subreg.cz/types). Register each method under the body
        # element's namespace as an alias so the dispatcher resolves both.
        for method_list in list(spyne_app.interface.service_method_map.values()):
            for method in method_list:
                in_ns = method.in_message.get_namespace()
                if in_ns and in_ns != spyne_app.tns:
                    alias_key = "{%s}%s" % (in_ns, method.name)
                    aliases = spyne_app.interface.service_method_map.setdefault(alias_key, [])
                    if method not in aliases:
                        aliases.append(method)

        app = ApiApplication(spyne_app, url)

        self.set_app(app)

    def handle_error(self, _request, client_address):
        if self.is_ssl:
            log.exception("HTTPS request handling from {} failed".format(client_address[0]))
        else:
            log.exception("HTTP request handling from {} failed".format(client_address[0]))
