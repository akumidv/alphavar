"""Instrument types"""
import enum
from alphavar.options.dictionary.enum_code import EnumCode


@enum.unique
class AssetType(EnumCode):
    """AssetType enumerates the different types of financial instruments supported.

    Examples:
        AssetType.SHARE.value -> 'share'
        AssetType.SHARE.code  -> 's'
    """
    SHARE = 'share', 's'
    COMMODITY = 'commodity', 'm'
    INDEX = 'index', 'i'
    CURRENCY = 'currency', 'c'
    CRYPTO = 'crypto', 'y'
