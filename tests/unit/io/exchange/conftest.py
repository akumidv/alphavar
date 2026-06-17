"""Hermetic exchange-test fixtures (T11): mock the HTTP layer with recorded responses.

Both Deribit and MOEX clients are wired to an httpx MockTransport that replays the
trimmed fixtures under `fixtures/<exchange>/` — no live API at test time. Refresh the
fixtures with `tools/exchange_fixtures` (record) + `tests/utils/exchange_fixtures/trim`.
"""
import httpx
import pytest

from alphavar.io.exchange import RequestClass
from alphavar.io.exchange.moex import MoexOptions, MoexExchange
from alphavar.io.exchange.deribit import DeribitExchange, DeribitMarket

from tests.utils.exchange_fixtures.mock import mock_transport


@pytest.fixture(name='moex_options_client')
def moex_options_fixture():
    """MOEX options client with a mocked transport (no network — T11)."""
    client = RequestClass(api_url=MoexExchange.TEST_API_URL)
    client.session = httpx.Client(transport=mock_transport('moex'))
    return MoexOptions(client)


@pytest.fixture(name='moex_exchange')
def moex_exchange_fixture():
    """MOEX exchange with a mocked transport (no network — T11). Overrides the
    network-hitting fixture in the root conftest."""
    moex = MoexExchange(api_url=MoexExchange.TEST_API_URL)
    moex.client.session = httpx.Client(transport=mock_transport('moex'))
    return moex


@pytest.fixture(name='deribit_market')
def deribit_market_fixture():
    """Deribit market client with a mocked transport (no network — T11)."""
    client = RequestClass(api_url=DeribitExchange.TEST_API_URL)
    client.session = httpx.Client(transport=mock_transport('deribit'))
    return DeribitMarket(client)


@pytest.fixture(name='deribit_client')
def deribit_client_fixture():
    """Deribit exchange with a mocked transport (no network — T11). Overrides the
    network-hitting fixture in the root conftest."""
    deribit = DeribitExchange(api_url=DeribitExchange.TEST_API_URL)
    deribit.client.session = httpx.Client(transport=mock_transport('deribit'))
    return deribit
