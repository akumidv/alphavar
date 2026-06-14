"""Record exchange HTTP fixtures from live APIs (needs network; run rarely).

    uv run python -m tools.exchange_fixtures              # all exchanges
    uv run python -m tools.exchange_fixtures --only moex

After recording, shrink the fixtures with the trimmer in tests/utils:
    uv run python -m tests.utils.exchange_fixtures.trim
"""
import argparse

from agents.tools.exchange_fixtures import deribit, moex

_EXCHANGES = {'deribit': deribit.run, 'moex': moex.run}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Record exchange API fixtures (needs network).')
    parser.add_argument('--only', choices=tuple(_EXCHANGES), help='Record just one exchange.')
    args = parser.parse_args(argv)
    for name, run in _EXCHANGES.items():
        if args.only in (None, name):
            run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
