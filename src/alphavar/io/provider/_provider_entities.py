"""Provider entities"""

import datetime
import enum

from pydantic import BaseModel

from alphavar.options.dictionary import Timeframe


class DataEngine(enum.Enum):
    """Data engines"""

    PANDAS = "pandas"
    POLARS = "polars"
    DASK = "dask"
    SPARK = "spark"


class DataSource(enum.Enum):
    """Source of data"""

    LOCAL = "local"
    S3 = "s3"
    API = "api"


class RequestParameters(BaseModel):
    """Parameters to request provider data"""

    period_from: int | datetime.date | datetime.datetime | None = None
    period_to: int | datetime.date | datetime.datetime | None = None
    timeframe: Timeframe = Timeframe.EOD
