"""Volatility-smile fitting tests (T21): SVI / quadratic / SABR + factory + no-arb."""

import numpy as np
import pytest

from alphavar.options.lib.pricer.smile import (
    DEFAULT_SMILE_MODEL,
    SMILE_MODELS,
    QuadraticSmile,
    SABRSmile,
    SVISmile,
    make_smile_model,
)

_T = 0.25


def _svi_iv(k, a=0.02, b=0.10, rho=-0.3, m=0.0, sigma=0.15, t=_T):
    """A known arbitrage-free SVI slice, in implied vol."""
    w = a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma**2))
    return np.sqrt(w / t)


@pytest.fixture(name="slice_pts")
def fixture_slice_pts():
    k = np.linspace(-0.6, 0.6, 15)
    return k, _svi_iv(k)


# --- factory ---------------------------------------------------------------------------------


def test_default_model_is_svi():
    assert DEFAULT_SMILE_MODEL == "svi"
    assert isinstance(make_smile_model(), SVISmile)


@pytest.mark.parametrize("name,cls", [("svi", SVISmile), ("quadratic", QuadraticSmile), ("sabr", SABRSmile)])
def test_factory_by_name(name, cls):
    assert isinstance(make_smile_model(name), cls)
    assert name in SMILE_MODELS


def test_factory_passthrough_instance():
    inst = SVISmile()
    assert make_smile_model(inst) is inst


def test_factory_unknown_raises():
    with pytest.raises(ValueError, match="Unknown smile model"):
        make_smile_model("garch")


# --- fit quality -----------------------------------------------------------------------------


def test_svi_recovers_known_slice(slice_pts):
    k, iv = slice_pts
    res = make_smile_model("svi").fit(k, iv, _T)
    assert np.sqrt(np.mean((res.iv(k) - iv) ** 2)) < 1e-3  # near-exact on a true SVI
    assert res.params["rho"] == pytest.approx(-0.3, abs=0.05)
    assert res.is_butterfly_free()


@pytest.mark.parametrize("name", ["svi", "quadratic", "sabr"])
def test_all_models_fit_reasonably(name, slice_pts):
    k, iv = slice_pts
    res = make_smile_model(name).fit(k, iv, _T)
    assert np.sqrt(np.mean((res.iv(k) - iv) ** 2)) < 0.02  # all track the smile
    assert np.all(res.iv(k) > 0)


def test_iv_is_non_negative_far_wings(slice_pts):
    k, iv = slice_pts
    res = make_smile_model("svi").fit(k, iv, _T)
    assert np.all(res.iv(np.array([-3.0, 3.0])) >= 0.0)


# --- degenerate inputs -----------------------------------------------------------------------


@pytest.mark.parametrize("name", ["svi", "quadratic", "sabr"])
def test_too_few_points_flat_fallback(name):
    k = np.array([-0.1, 0.1])
    iv = np.array([0.5, 0.6])
    res = make_smile_model(name).fit(k, iv, _T)
    out = res.iv(np.array([-0.2, 0.0, 0.2]))
    assert np.allclose(out, out[0])  # flat slice at the mean vol
    assert out[0] == pytest.approx(0.55, abs=1e-9)


@pytest.mark.parametrize("name", ["svi", "quadratic", "sabr"])
def test_nan_points_dropped(name, slice_pts):
    k, iv = slice_pts
    iv = iv.copy()
    iv[0] = np.nan
    k = k.copy()
    k[1] = np.inf
    res = make_smile_model(name).fit(k, iv, _T)
    assert np.isfinite(res.iv(0.0))


# --- no-arbitrage check ----------------------------------------------------------------------


def test_butterfly_free_true_for_arbitrage_free_svi(slice_pts):
    k, iv = slice_pts
    assert make_smile_model("svi").fit(k, iv, _T).is_butterfly_free()


def test_butterfly_check_flags_a_steep_skew_violation():
    # An overly steep skew breaks the wing (Lee) bound on total-variance slope → g(k) < 0.
    k = np.linspace(-0.6, 0.6, 15)
    iv = np.clip(0.4 + 2.0 * k, 0.05, None)  # slope 2.0 → arbitrageable
    res = make_smile_model("quadratic").fit(k, iv, _T)
    assert not res.is_butterfly_free()
