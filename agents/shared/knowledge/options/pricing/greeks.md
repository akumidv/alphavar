# Greeks

↑ Index: [options/pricing/](README.md)

> Source: Hull, *Options, Futures, and Other Derivatives* (Greek letters chapter).
> _Not yet implemented in alphavar (planned pricer, TASKS T21)._

Sensitivities of option value V to inputs:
- **Delta** `∂V/∂S` — directional exposure (calls 0…1, puts −1…0).
- **Gamma** `∂²V/∂S²` — convexity / how delta moves; largest near ATM, near expiry.
- **Vega** `∂V/∂σ` — sensitivity to implied volatility.
- **Theta** `∂V/∂t` — time decay (usually negative for long options).
- **Rho** `∂V/∂r` — sensitivity to the risk-free rate.

Portfolio risk aggregates Greeks across positions (see
[../../risk/](../../risk/README.md)). _Add closed-form Black-Scholes Greeks with source
when the pricer lands; owner-verify (D2)._
