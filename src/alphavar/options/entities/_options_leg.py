"""Option leg data class"""

from pydantic import BaseModel

from alphavar.options.dictionary import LegType


class OptionsLeg(BaseModel):
    """Option leg structure"""

    strike: float
    lots: int
    type: LegType
