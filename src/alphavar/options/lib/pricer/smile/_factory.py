"""Smile-model factory — pick a parametrization by name, default SVI (T21)."""
from __future__ import annotations

from alphavar.options.lib.pricer.smile._base import SmileModel
from alphavar.options.lib.pricer.smile.quadratic import QuadraticSmile
from alphavar.options.lib.pricer.smile.sabr import SABRSmile
from alphavar.options.lib.pricer.smile.svi import SVISmile

# registry of the available smile parametrizations (R5/T21)
SMILE_MODELS: dict[str, type[SmileModel]] = {
    SVISmile.name: SVISmile,
    QuadraticSmile.name: QuadraticSmile,
    SABRSmile.name: SABRSmile,
}
DEFAULT_SMILE_MODEL = SVISmile.name


def make_smile_model(name: str | SmileModel = DEFAULT_SMILE_MODEL) -> SmileModel:
    """Smile model by name (``"svi"`` default, ``"quadratic"``, ``"sabr"``); pass-through an instance."""
    if isinstance(name, SmileModel):
        return name
    try:
        return SMILE_MODELS[name]()
    except KeyError:
        raise ValueError(f"Unknown smile model {name!r}; available: {sorted(SMILE_MODELS)}") from None
