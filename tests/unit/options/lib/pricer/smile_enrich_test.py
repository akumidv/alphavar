"""DataFrame-level smile fitting tests (T21): add_smile_iv / fit_smile_slices."""

import numpy as np
import pandas as pd
import pytest

from alphavar.options.dictionary import OptionRight, OptionsTerm
from alphavar.options.lib.pricer._smile_enrich import add_smile_iv, fit_smile_slices


def _slice_frame(forward=100.0, t_days=90, ts="2025-01-01", asset="BTC"):
    """One option slice: a range of strikes with a known SVI mark-IV smile."""
    strikes = np.linspace(60, 160, 15)
    k = np.log(strikes / forward)
    t = t_days / 365.0
    w = 0.02 + 0.10 * (-0.3 * k + np.sqrt(k**2 + 0.15**2))  # arbitrage-free SVI
    iv = np.sqrt(w / t)
    timestamp = pd.Timestamp(ts, tz="UTC")
    expiration = timestamp + pd.Timedelta(days=t_days)
    return pd.DataFrame(
        {
            OptionsTerm.ASSET_CODE: asset,
            OptionsTerm.TIMESTAMP: timestamp,
            OptionsTerm.EXPIRATION_DATE: expiration,
            OptionsTerm.STRIKE: strikes,
            OptionsTerm.UNDERLYING_PRICE: forward,
            OptionsTerm.OPTION_RIGHT: OptionRight.CALL.value,
            OptionsTerm.EXCH_MARK_IV: iv,
        }
    )


def test_add_smile_iv_recovers_smile():
    df = _slice_frame()
    out = add_smile_iv(df, model="svi")
    assert OptionsTerm.IV in out.columns
    # fitted model IV tracks the (arbitrage-free) market smile closely
    assert np.sqrt(np.mean((out[OptionsTerm.IV] - df[OptionsTerm.EXCH_MARK_IV]) ** 2)) < 1e-3
    assert (out[OptionsTerm.IV] > 0).all()


def test_add_smile_iv_does_not_mutate_input():
    df = _slice_frame()
    before = df.copy()
    add_smile_iv(df, model="svi")
    pd.testing.assert_frame_equal(df, before)


@pytest.mark.parametrize("model", ["svi", "quadratic", "sabr"])
def test_add_smile_iv_all_models(model):
    df = _slice_frame()
    out = add_smile_iv(df, model=model)
    assert out[OptionsTerm.IV].notna().all()


def test_fit_smile_slices_one_per_slice():
    df = pd.concat(
        [_slice_frame(ts="2025-01-01"), _slice_frame(ts="2025-01-02"), _slice_frame(forward=50.0, asset="ETH")],
        ignore_index=True,
    )
    results = fit_smile_slices(df, model="svi")
    assert len(results) == 3  # (asset, expiration, timestamp) slices
    for res in results.values():
        assert res.is_butterfly_free()


def test_missing_market_iv_raises():
    df = _slice_frame().drop(columns=[OptionsTerm.EXCH_MARK_IV])
    with pytest.raises(KeyError, match="market-IV"):
        add_smile_iv(df, model="svi")


def test_facade_fit_smile_writes_iv_and_price(option_data):
    """End-to-end through the OptionsPricer facade over injected slice data."""
    from alphavar.options.pricer_class import OptionsPricer

    option_data.df_hist = _slice_frame()
    OptionsPricer(option_data).fit_smile(model="svi")
    assert OptionsTerm.IV in option_data.df_hist.columns
    assert OptionsTerm.PRICE in option_data.df_hist.columns
    assert option_data.df_hist[OptionsTerm.PRICE].notna().all()
