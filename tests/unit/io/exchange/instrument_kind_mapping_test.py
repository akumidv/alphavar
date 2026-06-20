"""Phase 1 (ADR 0001): venue-native kind token -> canonical (InstrumentKind, ContractKind)."""

import pytest

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.exchange.deribit import DeribitAssetKind, DeribitExchange
from alphavar.io.exchange.moex import MoexExchange
from alphavar.options.dictionary import ContractKind


def test_deribit_asset_kind_values_are_venue_native():
    # Singular venue spelling, used both as the API `kind=` param and the raw update token.
    assert DeribitAssetKind.OPTION.value == "option"
    assert DeribitAssetKind.FUTURE.value == "future"
    assert DeribitAssetKind.SPOT.value == "spot"
    assert DeribitAssetKind.OPTION_COMBO.value == "option_combo"
    assert DeribitAssetKind.FUTURE_COMBO.value == "future_combo"


@pytest.mark.parametrize(
    "native, expected",
    [
        ("option", (InstrumentKind.OPTION, ContractKind.VANILLA)),
        ("future", (InstrumentKind.FUTURE, ContractKind.VANILLA)),
        ("spot", (InstrumentKind.SPOT, ContractKind.VANILLA)),
        ("option_combo", (InstrumentKind.OPTION, ContractKind.COMBO)),
        ("future_combo", (InstrumentKind.FUTURE, ContractKind.COMBO)),
    ],
)
def test_deribit_resolve_instrument_kind(native, expected):
    assert DeribitExchange.resolve_instrument_kind(native) == expected


def test_deribit_resolve_unknown_kind_is_none():
    assert DeribitExchange.resolve_instrument_kind("warrant") is None


def test_moex_resolve_instrument_kind_is_identity():
    assert MoexExchange.resolve_instrument_kind("option") == (InstrumentKind.OPTION, ContractKind.VANILLA)
    assert MoexExchange.resolve_instrument_kind("future") == (InstrumentKind.FUTURE, ContractKind.VANILLA)
    assert MoexExchange.resolve_instrument_kind("spot") == (InstrumentKind.SPOT, ContractKind.VANILLA)
    assert MoexExchange.resolve_instrument_kind("option_combo") is None  # MOEX has no combos
