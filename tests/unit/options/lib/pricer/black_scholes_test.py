"""Black-76 pricer reference + round-trip tests (T21, pins the D2 math)."""

import numpy as np

from alphavar.options.lib.pricer import bs_forward_price, bs_vega, implied_vol, norm_cdf


def test_norm_cdf_known_values():
    assert float(norm_cdf(0.0)) == 0.5
    np.testing.assert_allclose(norm_cdf([0.0, 0.1, -0.1]), [0.5, 0.5398278, 0.4601722], atol=1e-6)


def test_atm_call_reference():
    # F=K=100, T=1, sigma=0.2, r=0 -> 7.9656 (hand-computed Black-76 ATM call).
    price = float(bs_forward_price(100.0, 100.0, 1.0, 0.2, True))
    np.testing.assert_allclose(price, 7.965567, atol=1e-4)


def test_put_call_parity_zero_rate():
    # call - put = e^{-rT}(F - K); with r=0 -> F - K.
    f, k = 105.0, 100.0
    call = float(bs_forward_price(f, k, 0.75, 0.3, True))
    put = float(bs_forward_price(f, k, 0.75, 0.3, False))
    np.testing.assert_allclose(call - put, f - k, atol=1e-9)


def test_implied_vol_round_trip():
    f, k, t, sig = 100.0, 110.0, 0.5, 0.35
    for is_call in (True, False):
        px = bs_forward_price(f, k, t, sig, is_call)
        iv = float(implied_vol(px, f, k, t, is_call))
        np.testing.assert_allclose(iv, sig, atol=1e-6)


def test_implied_vol_vectorized():
    f = np.array([100.0, 100.0, 100.0])
    k = np.array([90.0, 100.0, 110.0])
    sig = np.array([0.25, 0.30, 0.40])
    px = bs_forward_price(f, k, 1.0, sig, True)
    iv = implied_vol(px, f, k, 1.0, True)
    np.testing.assert_allclose(iv, sig, atol=1e-6)


def test_degenerate_inputs_give_intrinsic():
    # T=0 and sigma=0 both collapse to (discounted) intrinsic.
    assert float(bs_forward_price(120.0, 100.0, 0.0, 0.3, True)) == 20.0  # call intrinsic
    assert float(bs_forward_price(80.0, 100.0, 1.0, 0.0, False)) == 20.0  # put intrinsic, no vol
    assert float(bs_forward_price(120.0, 100.0, 1.0, 0.0, False)) == 0.0  # OTM put, no vol


def test_implied_vol_outside_bracket_is_nan():
    # A price below intrinsic has no implied vol.
    below_intrinsic = 5.0  # call intrinsic is 20 for F=120,K=100
    assert np.isnan(float(implied_vol(below_intrinsic, 120.0, 100.0, 1.0, True)))


def test_vega_positive_atm():
    assert float(bs_vega(100.0, 100.0, 1.0, 0.2)) > 0.0
    assert float(bs_vega(100.0, 100.0, 0.0, 0.2)) == 0.0  # no time -> no vega
