"""alphavar.options — options & futures domain (R0).

Internal shape, by layer then function:
- facade (flat at this root): ``Option`` and its components (``OptionData``,
  ``OptionEnrichment``, ``OptionChain``, ``OptionAnalytic``, ``ChartClass`` …);
- ``dictionary`` / ``entities`` / ``schemas`` — domain foundation;
- ``lib`` — pure computational logic, by function;
- ``etl`` — I/O orchestration.
"""
from alphavar.options.option_class import Option
from alphavar.options.option_data_class import OptionData
from alphavar.options.enrichment_class import OptionEnrichment
from alphavar.options.chain_class import OptionChain
from alphavar.options.analytic_class import OptionAnalytic
from alphavar.options.analytic_price_class import OptionAnalyticPrice
from alphavar.options.analytic_risk_class import OptionAnalyticRisk
from alphavar.options.chart_class import ChartClass
from alphavar.options.chart_price_class import ChartPriceClass

__all__ = [
    "Option", "OptionData", "OptionEnrichment", "OptionChain",
    "OptionAnalytic", "OptionAnalyticPrice", "OptionAnalyticRisk",
    "ChartClass", "ChartPriceClass",
]
