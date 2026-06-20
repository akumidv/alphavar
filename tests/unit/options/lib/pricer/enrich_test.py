"""DataFrame pricer enrichment: round-trip price -> iv (T21, pins the D2 wiring)."""

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.pricer import add_fair_price, add_model_iv, years_to_expiry


def _df(sigmas):
    n = len(sigmas)
    ts = pd.Timestamp("2025-01-01", tz="UTC")
    return pd.DataFrame(
        {
            OptionsTerm.TIMESTAMP: [ts] * n,
            OptionsTerm.EXPIRATION_DATE: [ts + pd.Timedelta(days=365)] * n,  # T = 1 year
            OptionsTerm.UNDERLYING_PRICE: [100.0] * n,
            OptionsTerm.STRIKE: [90.0, 100.0, 110.0][:n],
            OptionsTerm.OPTION_RIGHT: ["call", "put", "call"][:n],
            "_sigma": sigmas,
        }
    )


def test_years_to_expiry_one_year():
    ts = pd.Timestamp("2025-01-01", tz="UTC")
    s = years_to_expiry(pd.Series([ts + pd.Timedelta(days=365)]), pd.Series([ts]))
    np.testing.assert_allclose(s.to_numpy(), [1.0], atol=1e-9)
    # expired -> clipped to 0
    s2 = years_to_expiry(pd.Series([ts - pd.Timedelta(days=10)]), pd.Series([ts]))
    assert float(s2.iloc[0]) == 0.0


def test_price_then_iv_round_trip():
    sigmas = [0.25, 0.35, 0.45]
    df = _df(sigmas)
    # price each row at its known sigma, then recover iv from that price.
    priced = add_fair_price(df, vol_col="_sigma", out_col=OptionsTerm.EXCH_MARK_PRICE)
    out = add_model_iv(priced)  # iv from exch_mark_price
    np.testing.assert_allclose(out[OptionsTerm.IV].to_numpy(), sigmas, atol=1e-6)


def test_add_model_iv_is_pure():
    df = _df([0.3])
    df = add_fair_price(df, vol_col="_sigma", out_col=OptionsTerm.EXCH_MARK_PRICE)
    before = set(df.columns)
    _ = add_model_iv(df)
    assert set(df.columns) == before  # input frame untouched (returns a copy)
