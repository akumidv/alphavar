# VaR methods

↑ Index: [risk/var/](README.md)

> Source: Hull (VaR chapter).

- **Historical simulation:** apply the empirical distribution of past returns to the
  current portfolio; VaR = the α-quantile of simulated P&L. No distributional assumption;
  needs enough representative history; poor on unseen regimes.
- **Parametric (variance-covariance / delta-normal):** assume returns ~ Normal; VaR
  `= zₐ · σ_portfolio` (× horizon scaling). Fast; weak for fat tails and non-linear
  (option) payoffs unless delta-gamma adjusted.
- **Monte-Carlo:** simulate many price paths from a chosen model, full-revalue the
  portfolio, take the α-quantile. Handles non-linearity/path-dependence; compute-heavy.

For option portfolios, full revaluation (historical/MC) captures convexity better than
delta-normal. _Owner-verify (D2) the implementation when added._
