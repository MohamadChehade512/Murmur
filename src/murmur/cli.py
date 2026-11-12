"""Command line: `murmur run` does one full collection and publishes the summary."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import DEFAULT_PATH, load_companies
from .pipeline import run
from .sentiment import get_backend
from .store import Store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="murmur", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="collect, score, store and publish once")
    r.add_argument("--config", type=Path, default=DEFAULT_PATH, help="companies.toml")
    r.add_argument("--data", type=Path, default=Path("data"), help="storage folder (the data branch)")
    r.add_argument("--out", type=Path, default=Path("public"), help="folder to publish")
    r.add_argument("--hours", type=int, default=6, help="how far back to look each run")
    r.add_argument("--sentiment", choices=("lexicon", "model"), default="lexicon")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    stats = run(
        load_companies(args.config),
        Store(args.data),
        args.out,
        get_backend(args.sentiment),
        hours=args.hours,
    )
    return 0 if stats.collected or stats.added else 1


if __name__ == "__main__":
    raise SystemExit(main())
