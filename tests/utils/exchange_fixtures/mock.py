"""Replay recorded exchange fixtures via an httpx MockTransport (hermetic tests, T11).

`mock_transport(name)` reads ``tests/unit/exchange/fixtures/<name>/index.json`` (path+query
-> body file) and returns an ``httpx.MockTransport`` that serves those bodies. Used by the
exchange-test conftest so the suite never hits a live API.
"""
from __future__ import annotations

import json
import os

import httpx

FIXTURES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'unit', 'exchange', 'fixtures')
)


def _request_key(url) -> str:
    """Must match the recorder's key: path + sorted query (drop volatile params)."""
    params = sorted((k, v) for k, v in url.params.multi_items() if k not in ('timestamp',))
    query = '&'.join(f'{k}={v}' for k, v in params)
    return f'{url.path}?{query}' if query else url.path


def _load_index(name: str) -> dict[str, tuple[int, object]]:
    """Map request key -> (status, body). Index entries are ``{file, status}`` (current)
    or a bare filename string (legacy → assumed 200)."""
    base = os.path.join(FIXTURES_ROOT, name)
    with open(os.path.join(base, 'index.json'), encoding='utf-8') as f:
        index = json.load(f)
    out = {}
    for key, entry in index.items():
        if isinstance(entry, dict):
            fn, status = entry['file'], entry.get('status', 200)
        else:
            fn, status = entry, 200
        with open(os.path.join(base, fn), encoding='utf-8') as f:
            out[key] = (status, json.load(f))
    return out


def mock_transport(name: str) -> httpx.MockTransport:
    """An httpx transport that replays recorded responses (with their status) for
    exchange ``name`` — so the client's non-2xx handling (e.g. 422) is exercised too."""
    responses = _load_index(name)

    def handler(request: httpx.Request) -> httpx.Response:
        entry = responses.get(_request_key(request.url))
        if entry is None:
            return httpx.Response(404, json={'error': f'no fixture for {request.url.path}'})
        status, body = entry
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)
