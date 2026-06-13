import pytest
from alphavar.options_lib.normalization import validate_path_segment


@pytest.mark.parametrize('value', ['BTC', 'ETH_USDC', 'BTCDVOL_USDC', 'DERIBIT', 'a.b-c', '2025'])
def test_validate_path_segment_accepts_valid(value):
    assert validate_path_segment(value) == value


@pytest.mark.parametrize('value', [
    '..', '.', '../etc', 'a/b', 'a\\b', '/abs', 'BTC/../ETH',
    '', 'a b', 'a;b', 'a$b', 'a:b',
])
def test_validate_path_segment_rejects_unsafe(value):
    with pytest.raises(ValueError):
        validate_path_segment(value)


def test_validate_path_segment_rejects_non_str():
    with pytest.raises(ValueError):
        validate_path_segment(None)


def test_validate_path_segment_field_in_message():
    with pytest.raises(ValueError, match='asset_code'):
        validate_path_segment('../x', field='asset_code')
