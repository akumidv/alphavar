"""Option leg data class"""

import enum

from alphavar.options.dictionary._options_types import OptionsType
from alphavar.options.dictionary.enum_code import EnumCode


@enum.unique
class LegType(EnumCode):
    """
    Usage code for legs
    """

    OPTIONS_CALL = OptionsType.CALL.value, OptionsType.CALL.code
    OPTIONS_PUT = OptionsType.PUT.value, OptionsType.PUT.code
    FUTURES = "futures", "f"
