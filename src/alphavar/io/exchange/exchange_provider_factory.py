"""
A Factory function constructs a provider depending on the storage and engine chosen
"""

from functools import partial

from alphavar.io.exchange.exchange_fabric import get_exchange
from alphavar.io.provider import AbstractProvider, DataEngine, DataSource, PandasLocalFileProvider

_PROVIDERS: dict[DataSource, dict[DataEngine, type[AbstractProvider]]] = {
    DataSource.LOCAL: {
        DataEngine.PANDAS: PandasLocalFileProvider,
        DataEngine.POLARS: AbstractProvider,
        DataEngine.DASK: AbstractProvider,
        DataEngine.SPARK: AbstractProvider,
    },
    DataSource.S3: {
        DataEngine.PANDAS: AbstractProvider,
        DataEngine.POLARS: AbstractProvider,
        DataEngine.DASK: AbstractProvider,
        DataEngine.SPARK: AbstractProvider,
    },
    DataSource.API: {
        DataEngine.PANDAS: partial(get_exchange, engine=DataEngine.PANDAS),
        DataEngine.POLARS: partial(get_exchange, engine=DataEngine.POLARS),
        DataEngine.DASK: partial(get_exchange, engine=DataEngine.DASK),
        DataEngine.SPARK: partial(get_exchange, engine=DataEngine.SPARK),
    },
}


def get_provider(
    exchange_code, storage: DataSource = DataSource.LOCAL, engine: DataEngine = DataEngine.PANDAS, **kwargs
) -> AbstractProvider:
    """Provider fabric"""
    return _PROVIDERS[storage][engine](exchange_code=exchange_code, **kwargs)
