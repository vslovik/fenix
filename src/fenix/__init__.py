"""fenix — a discovery tool for reading the state of a market.

Three commands, one corpus:

    fenix scan            rank the incoming stream against position descriptions
    fenix ingest          fetch article text, chunk, embed, store
    fenix ask "question"  answer from the corpus, citing the chunks used
"""

import sys


def main() -> None:
    args = sys.argv[1:]
    command = args[0] if args else ""

    if command == "scan":
        from .signal_scan import scan
        scan()
    elif command == "ingest":
        from .ingest import ingest
        limit = int(args[1]) if len(args) > 1 else None
        ingest(limit)
    elif command == "ask":
        from .ask import ask
        question = " ".join(a for a in args[1:] if a != "--show-chunks")
        if not question:
            print('Usage: fenix ask "your question" [--show-chunks]')
            sys.exit(1)
        ask(question, show_chunks="--show-chunks" in args)
    elif command == "reindex":
        from . import store
        from .embedding import embed
        n = store.reindex(store.connect(), embed)
        print(f"re-embedded {n} chunk(s)")
    elif command == "stats":
        from . import store
        print(store.stats(store.connect()))
    else:
        print(__doc__.strip())
        sys.exit(0 if command in ("", "-h", "--help") else 1)