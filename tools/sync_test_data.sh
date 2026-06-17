#!/usr/bin/env bash
#
# Sync the minimal market-data slice the test suite needs into the local data store.
#
# The hermetic unit suite (T11) mocks the exchange HTTP layer, but a handful of tests
# still read parquet files from DATA_PATH:
#   * provider / chain / enrichment / analytics tests -> EOD *history*
#   * tests/unit/options/etl/etl_history_test.py       -> *update* files
# All of them use exchange_code=DERIBIT and option_symbol=BTC (see tests/conftest.py),
# so we only copy DERIBIT/BTC — MOEX is exercised through the (mocked/live) API, not files.
#
# Usage:
#   tools/sync_test_data.sh SRC [DST] [--apply]
#
#   SRC   full data store to copy from. Local path or remote, e.g.
#           /home/ak/Workspace/.../alphavar/data
#           ak@workstation:/home/ak/Workspace/.../alphavar/data
#   DST   where the tests read from. Default: the repo-local ./data
#           (point test.env's DATA_PATH here, or pass your DATA_PATH as DST).
#
# Without --apply the script does a --dry-run so you can review what would transfer.
#
# Override the slice with env vars, e.g.  EXCHANGE=DERIBIT SYMBOL=ETH INCLUDE_SPOT=1
set -euo pipefail

EXCHANGE="${EXCHANGE:-DERIBIT}"   # must match tests/conftest.py exchange_code (upper-case)
SYMBOL="${SYMBOL:-BTC}"           # must match tests/conftest.py option_symbol
INCLUDE_SPOT="${INCLUDE_SPOT:-0}" # tests don't need spot; set 1 to include it

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SRC="${1:-}"
DST="${2:-$repo_root/data}"
APPLY=0
for arg in "$@"; do [ "$arg" = "--apply" ] && APPLY=1; done
# Treat a positional --apply as a flag, not as DST.
[ "${DST:-}" = "--apply" ] && DST="$repo_root/data"

if [ -z "$SRC" ]; then
  sed -n '2,30p' "${BASH_SOURCE[0]}"
  echo "ERROR: SRC is required." >&2
  exit 2
fi

# rsync needs trailing slashes so contents (not the dir itself) are merged into DST.
SRC="${SRC%/}/"
DST="${DST%/}/"

filters=(
  # --- EOD history: EXCHANGE/SYMBOL/{options,futures}[/spot]/EOD/*.parquet ---
  "--include=/${EXCHANGE}/"
  "--include=/${EXCHANGE}/${SYMBOL}/"
  "--include=/${EXCHANGE}/${SYMBOL}/options/"
  "--include=/${EXCHANGE}/${SYMBOL}/options/EOD/***"
  "--include=/${EXCHANGE}/${SYMBOL}/futures/"
  "--include=/${EXCHANGE}/${SYMBOL}/futures/EOD/***"
  # --- update files: update/EXCHANGE/SYMBOL/{options,futures}/<timeframe>/... ---
  "--include=/update/"
  "--include=/update/${EXCHANGE}/"
  "--include=/update/${EXCHANGE}/${SYMBOL}/"
  "--include=/update/${EXCHANGE}/${SYMBOL}/options/***"
  "--include=/update/${EXCHANGE}/${SYMBOL}/futures/***"
)
if [ "$INCLUDE_SPOT" = "1" ]; then
  filters+=(
    "--include=/${EXCHANGE}/${SYMBOL}/spot/"
    "--include=/${EXCHANGE}/${SYMBOL}/spot/EOD/***"
    "--include=/update/${EXCHANGE}/${SYMBOL}/spot/***"
  )
fi
filters+=("--exclude=*")   # everything not whitelisted above is skipped

rsync_opts=(-a --prune-empty-dirs --human-readable --info=stats1,progress2)
[ "$APPLY" -eq 1 ] || rsync_opts+=(--dry-run)

echo "SRC : $SRC"
echo "DST : $DST"
echo "Slice: ${EXCHANGE}/${SYMBOL} (options+futures EOD + updates$([ "$INCLUDE_SPOT" = 1 ] && echo ' + spot'))"
[ "$APPLY" -eq 1 ] && echo "Mode: APPLY" || echo "Mode: DRY-RUN (re-run with --apply to transfer)"
echo

mkdir -p "$DST"
set -x
rsync "${rsync_opts[@]}" "${filters[@]}" "$SRC" "$DST"
