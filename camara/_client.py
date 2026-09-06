"""
Shared Nokia Network-as-Code client factory.
Every camara/*.py module gets its client from here so there's one place
that knows how auth actually works.
"""
from network_as_code import NetworkAsCodeApi
import config

_client = None


def get_client() -> NetworkAsCodeApi:
    global _client
    if _client is None:
        config.require("NOKIA_API_KEY")
        _client = NetworkAsCodeApi(
            rapidapi_host=config.NOKIA_RAPIDAPI_HOST,
            api_key=config.NOKIA_API_KEY,
        )
    return _client
