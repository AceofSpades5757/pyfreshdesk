from __future__ import annotations

import functools
import logging.config
from abc import ABC
from types import SimpleNamespace
from typing import Optional
from typing import Protocol
from typing import Type
from typing import Union

from freshdesk.enumerators import HTTPRequestMethod
from freshdesk.logger import get_config


""" Logging """
logging.config.dictConfig(get_config(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_interface(function):
    function.register = True

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        function.register = True

        return function(*args, **kwargs)

    return wrapper


class API(Protocol):
    name: Optional[str] = None
    client: Optional[Type[Client]] = None

    @classmethod
    def _init_client(cls, client: Type[Client] = None) -> None:
        cls.client = client
        ...

    def _register_interfaces(self) -> None: ...


class Client(Protocol):
    api: SimpleNamespace

    def __init__(self):
        self._initialize_apis()
        ...

    def _initialize_apis(self) -> None:
        for api in self.api.__dict__:
            APIClass = getattr(self.api, api)
            api_instance = APIClass(self)

            setattr(self.api, api, api_instance)
        ...

    @classmethod
    def register_api(cls, api: Type[API]) -> None: ...


class BaseClient(ABC):
    api: SimpleNamespace = SimpleNamespace()

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._initialize_apis()
        return instance

    def _initialize_apis(self) -> None:
        for api in self.api.__dict__:
            APIClass = getattr(self.api, api)
            api_instance = APIClass(self)

            api_instance.client = self
            setattr(self.api, api, api_instance)

    @classmethod
    def register_api(cls, api: Type[API]) -> None:
        # Init Client with API
        api._init_client(cls)

        # Add API to self.api
        api_name = getattr(api, "name", api.__name__)  # type: ignore
        setattr(cls.api, api_name, api)


class BaseAPI(ABC):
    client = None
    path = "/"

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.client = getattr(instance, "client", None)
        instance._register_interfaces()
        return instance

    @classmethod
    def _init_client(cls, client):
        cls.client = client

    @property
    def base_url(self):
        if self.client is not None:
            return self.client.base_url + self.path

        return "https://domain.freshdesk.com/"

    def _register_interfaces(self) -> None:
        # Register Intefaces to Client
        for function_name in (f for f in dir(self) if not f.startswith("_")):
            try:
                function = getattr(self, function_name)
            except Exception:  # Hotfix for errors with properties
                continue
            register = getattr(function, "register", False)

            if register:
                setattr(self.client, function.__name__, function)

    def _request(
        self, url: str, method: Union[str, HTTPRequestMethod] = "GET", **kwargs
    ):
        return self.client._request(url=url, method=method, **kwargs)
