# SPDX-License-Identifier: EUPL-1.2
from abc import ABC, abstractmethod
from typing import Any, Callable, Union

from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.wsse.signature import Signature
from zeep.xsd import AnySimpleType, ComplexType

_NAMESPACE = "ns0"


class AbstractService(ABC):
    @abstractmethod
    def init_client(self):
        pass  # pragma: no cover

    @abstractmethod
    def init_service(self):
        pass  # pragma: no cover

    @abstractmethod
    def call_api(self, message: Union[ComplexType, AnySimpleType]):
        pass  # pragma: no cover


class AbstractSOAPService(AbstractService, ABC):
    def __init__(self, wsdl_file: str):
        super().__init__()

        self.wsdl = wsdl_file

        self.session = Session()
        self.transport = Transport(session=self.session)

        self.client: Client

        self.init_client()
        self.factory = self.client.type_factory(_NAMESPACE)

        self.service: Callable
        self.init_service()

    def call_api(self, message: Union[ComplexType, AnySimpleType]) -> Any:
        # For debugging, set debug level for zeep in config to debug.
        return self.service(message)


class AbstractSecureSOAPService(AbstractSOAPService, ABC):
    def __init__(self, wsdl_file: str, signature: Signature = None, cert_file: str = None):
        # cert & key must be combined; and according to the documentation at
        # "https://requests.readthedocs.io/en/master/user/advanced/" cannot be encrypted (docs: "Warning
        # The private key to your local certificate must be unencrypted. Currently, Requests does not support using
        # encrypted keys.").
        self.cert = cert_file
        self.signature = signature

        super().__init__(wsdl_file)
        self.session.cert = self.cert

    def init_client(self):
        self.client = Client(wsdl=self.wsdl, transport=self.transport, wsse=self.signature)
