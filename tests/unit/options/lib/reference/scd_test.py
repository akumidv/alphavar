"""SCD Type 2 reference history: append_on_change + as_of (T25)."""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.reference import append_on_change, as_of, join_reference_asof

KEY = [OptionsTerm.EXCH_SYMBOL]
ATTR = [OptionsTerm.OPTION_STYLE]
T1 = pd.Timestamp("2025-01-01", tz="UTC")
T2 = pd.Timestamp("2025-02-01", tz="UTC")
T3 = pd.Timestamp("2025-03-01", tz="UTC")


def _snap(rows):
    return pd.DataFrame(rows, columns=[OptionsTerm.EXCH_SYMBOL, OptionsTerm.OPTION_STYLE])


def test_first_observation_opens_records():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"], ["B", "european"]]), T1, KEY, ATTR)
    assert len(hist) == 2
    assert hist[OptionsTerm.VALID_FROM].eq(T1).all()
    assert hist[OptionsTerm.VALID_TO].isna().all()  # both open


def test_unchanged_snapshot_is_noop():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    hist2 = append_on_change(hist, _snap([["A", "european"]]), T2, KEY, ATTR)
    assert len(hist2) == 1  # no new version
    assert hist2[OptionsTerm.VALID_TO].isna().all()


def test_new_key_appends_open_record():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    hist2 = append_on_change(hist, _snap([["A", "european"], ["B", "american"]]), T2, KEY, ATTR)
    assert len(hist2) == 2
    b = hist2[hist2[OptionsTerm.EXCH_SYMBOL] == "B"].iloc[0]
    assert b[OptionsTerm.VALID_FROM] == T2 and pd.isna(b[OptionsTerm.VALID_TO])


def test_changed_attribute_closes_old_and_opens_new():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    hist2 = append_on_change(hist, _snap([["A", "american"]]), T2, KEY, ATTR)
    a = hist2[hist2[OptionsTerm.EXCH_SYMBOL] == "A"].sort_values(OptionsTerm.VALID_FROM)
    assert len(a) == 2
    old, new = a.iloc[0], a.iloc[1]
    assert old[OptionsTerm.OPTION_STYLE] == "european" and old[OptionsTerm.VALID_TO] == T2
    assert new[OptionsTerm.OPTION_STYLE] == "american" and pd.isna(new[OptionsTerm.VALID_TO])


def test_missing_key_left_open():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"], ["B", "european"]]), T1, KEY, ATTR)
    hist2 = append_on_change(hist, _snap([["A", "european"]]), T2, KEY, ATTR)  # B absent
    b = hist2[hist2[OptionsTerm.EXCH_SYMBOL] == "B"].iloc[0]
    assert pd.isna(b[OptionsTerm.VALID_TO])  # not auto-expired


def test_as_of_selects_the_valid_version():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    hist = append_on_change(hist, _snap([["A", "american"]]), T2, KEY, ATTR)
    # before the change -> european; after -> american
    assert as_of(hist, T1, KEY).iloc[0][OptionsTerm.OPTION_STYLE] == "european"
    assert as_of(hist, T3, KEY).iloc[0][OptionsTerm.OPTION_STYLE] == "american"
    # at the boundary T2 (exclusive valid_to) -> the new version
    assert as_of(hist, T2, KEY).iloc[0][OptionsTerm.OPTION_STYLE] == "american"
    # before any record -> empty
    assert as_of(hist, pd.Timestamp("2024-01-01", tz="UTC"), KEY).empty


def test_join_reference_asof_attaches_version_valid_at_each_row_time():
    # contract A: european on [T1, T2), american on [T2, open)
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    hist = append_on_change(hist, _snap([["A", "american"]]), T2, KEY, ATTR)
    # slim quotes (no option_style) for A at three times
    quotes = pd.DataFrame(
        {OptionsTerm.EXCH_SYMBOL: ["A", "A", "A"], OptionsTerm.TIMESTAMP: [T1, T2, T3]}
    )
    out = join_reference_asof(quotes, hist, KEY, OptionsTerm.TIMESTAMP)
    assert list(out[OptionsTerm.OPTION_STYLE]) == ["european", "american", "american"]


def test_join_reference_asof_no_overwrite_and_unmatched_is_nan():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    # row for A (before T1 -> no covering version) and B (no key at all) -> ref NaN, row kept
    quotes = pd.DataFrame(
        {
            OptionsTerm.EXCH_SYMBOL: ["A", "B"],
            OptionsTerm.TIMESTAMP: [pd.Timestamp("2024-01-01", tz="UTC"), T2],
        }
    )
    out = join_reference_asof(quotes, hist, KEY, OptionsTerm.TIMESTAMP)
    assert len(out) == 2
    assert out[OptionsTerm.OPTION_STYLE].isna().all()


def test_join_reference_asof_is_noop_when_column_present():
    hist = append_on_change(pd.DataFrame(), _snap([["A", "european"]]), T1, KEY, ATTR)
    wide = pd.DataFrame(
        {OptionsTerm.EXCH_SYMBOL: ["A"], OptionsTerm.TIMESTAMP: [T2], OptionsTerm.OPTION_STYLE: ["custom"]}
    )
    out = join_reference_asof(wide, hist, KEY, OptionsTerm.TIMESTAMP)
    assert list(out[OptionsTerm.OPTION_STYLE]) == ["custom"]  # already-present column untouched
