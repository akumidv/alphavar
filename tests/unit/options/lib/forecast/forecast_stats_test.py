"""Pure-numpy stats helpers for forecasting (T27): inverse-normal CDF + lognormal terminal."""

import numpy as np

from alphavar.options.lib.forecast._stats import LogNormalTerminal, norm_ppf
from alphavar.options.lib.pricer.black_scholes import norm_cdf


def test_norm_ppf_inverts_norm_cdf():
    q = np.linspace(0.001, 0.999, 99)
    assert np.allclose(norm_cdf(norm_ppf(q)), q, atol=1e-6)


def test_norm_ppf_known_points():
    assert abs(float(norm_ppf(0.5))) < 1e-9
    assert np.isclose(float(norm_ppf(0.975)), 1.959963985, atol=1e-6)
    assert np.isclose(float(norm_ppf(0.025)), -1.959963985, atol=1e-6)


def test_norm_ppf_out_of_domain_is_nan():
    assert np.isnan(norm_ppf(0.0))
    assert np.isnan(norm_ppf(1.0))


def test_lognormal_mean_ppf_and_sample():
    meanlog, sdlog = np.log(100.0), 0.2
    dist = LogNormalTerminal(meanlog, sdlog)
    assert np.isclose(dist.mean(), np.exp(meanlog + 0.5 * sdlog**2))
    assert np.isclose(dist.ppf(0.5), np.exp(meanlog))  # median = exp(μ)
    sample = dist.sample(200_000, np.random.default_rng(0))
    assert np.isclose(sample.mean(), dist.mean(), rtol=0.02)
    assert np.all(sample > 0.0)
