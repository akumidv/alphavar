"""Abstract exchange class module"""

import time
from abc import ABC, abstractmethod
from typing import NamedTuple
import httpx
import pandas as pd

from alphavar.io.provider import DataEngine
from alphavar.io.provider import AbstractProvider
from alphavar.io.exchange.exchange_exception import APIException, RequestException
from alphavar.core.dictionary import InstrumentKind, ContractKind


class BookData(NamedTuple):
    """Book data snapshot"""
    option: pd.DataFrame | None
    future: pd.DataFrame | None
    spot: pd.DataFrame | None


class RequestClass:
    """Request implementation for Exchanges"""
    api_url: str
    version_url: str | None = None
    HEADERS: dict = {
        'Accept': 'application/json',
        'User-Agent': 'Option Library Client',
    }
    # Retry policy for transient failures (rate limiting and server errors).
    MAX_RETRIES: int = 3
    BACKOFF_BASE_SEC: float = 1.0
    BACKOFF_MAX_SEC: float = 30.0
    RETRY_STATUS: frozenset = frozenset({429, 500, 502, 503, 504})

    def __init__(self, api_url, http_params: dict | None = None):
        self.api_url = api_url[:-1] if api_url[-1] == '/' else api_url
        if not isinstance(http_params, dict):
            http_params = {'headers': self.HEADERS}
        elif 'headers' not in http_params:
            http_params['headers'] = self.HEADERS
        self.session = httpx.Client(**http_params)
        self.timestamp_offset = 0

    def request_api(self, endpoint_path: str, signed: bool = False, **kwargs):
        """Main request method.

        ``signed`` (authenticated/private endpoints) is not implemented — only public
        endpoints are supported. Passing ``signed=True`` raises rather than silently
        sending an unauthenticated request.
        """
        if signed:
            raise NotImplementedError('Signed (authenticated) requests are not supported; '
                                      'only public endpoints are available.')
        api_url = self._create_api_uri(endpoint_path)
        return self._request(api_url, **kwargs)

    def _request(self, request_url, **kwargs):
        last_retryable: httpx.Response | httpx.HTTPError | None = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.session.get(request_url, **kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as err:
                last_retryable = err
            else:
                if response.status_code not in self.RETRY_STATUS:
                    return self._handle_response(response)
                last_retryable = response
            if attempt < self.MAX_RETRIES:
                time.sleep(self._retry_delay(attempt, last_retryable))
        # Retries exhausted — surface the last failure.
        if isinstance(last_retryable, httpx.Response):
            return self._handle_response(last_retryable)
        raise RequestException(f'Request failed after {self.MAX_RETRIES} retries: '
                               f'{type(last_retryable).__name__}') from last_retryable

    def _retry_delay(self, attempt: int, last: 'httpx.Response | httpx.HTTPError | None') -> float:
        """Exponential backoff, honoring a 429 ``Retry-After`` header when present."""
        if isinstance(last, httpx.Response) and last.status_code == 429:
            retry_after = last.headers.get('Retry-After')
            if retry_after and retry_after.isdigit():
                return min(float(retry_after), self.BACKOFF_MAX_SEC)
        return min(self.BACKOFF_BASE_SEC * (2 ** attempt), self.BACKOFF_MAX_SEC)

    @staticmethod
    def _handle_response(response: httpx.Response):
        """Internal helper for handling API responses.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        parsed JSON body.
        """
        if not str(response.status_code).startswith('2'):
            raise APIException(response, response.status_code, response.text)
        try:
            return response.json()
        except ValueError as err:
            raise RequestException(f'Invalid Response: {err}\n{response.text}: ') from err

    def _create_api_uri(self, endpoint_path: str) -> str:
        endpoint_path = endpoint_path if endpoint_path[0] != '/' else endpoint_path[1:]
        return f'{self.api_url}/{endpoint_path}'


class AbstractExchange(AbstractProvider, ABC):
    """Abstract exchange class"""
    SOURCE_PREFIX = 'source'

    # Venue-native asset-kind token (as stored in the raw update layout and the venue API,
    # e.g. Deribit 'option'/'future_combo') -> canonical (InstrumentKind, ContractKind).
    # The canon is a project enum, kept separate from the venue wire format (R2.2); the
    # raw update store stays venue-native and is normalized here at the migration boundary
    # (ADR 0001 / R4.5). Subclasses override this map; empty by default.
    INSTRUMENT_KIND_MAP: dict[str, tuple[InstrumentKind, ContractKind]] = {}

    @classmethod
    def resolve_instrument_kind(cls, native_kind: str) -> tuple[InstrumentKind, ContractKind] | None:
        """Resolve a venue-native kind token to the canonical (InstrumentKind, ContractKind),
        or None if the venue token is unknown to this exchange."""
        return cls.INSTRUMENT_KIND_MAP.get(native_kind)

    @abstractmethod
    def __init__(self, engine: DataEngine, exchange_code: str, api_url: str, http_params: dict | None = None, **kwargs):
        """"""
        self.client = RequestClass(api_url, http_params)
        super().__init__(exchange_code, **kwargs)

    @abstractmethod
    def get_options_assets_books_snapshot(self, asset_codes: list[str] | str | None = None) -> pd.DataFrame:
        """Get symbols books snapshot"""
