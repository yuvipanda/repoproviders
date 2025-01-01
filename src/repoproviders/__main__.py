import argparse
import asyncio
import sys
from pathlib import Path

from .fetchers import fetch
from .resolvers import resolve


async def main():
    argparser = argparse.ArgumentParser()

    subparsers = argparser.add_subparsers(required=True, dest="command")
    resolve_subparser = subparsers.add_parser("resolve")

    resolve_subparser.add_argument("question", help="What should we try to resolve?")
    resolve_subparser.add_argument(
        "--no-recurse",
        help="Do not recurse, return after first answer",
        action="store_true",
    )

    fetch_subparser = subparsers.add_parser("fetch")
    fetch_subparser.add_argument("question", help="What should we try to fetch?")
    fetch_subparser.add_argument("output_dir", help="Where to output the fetched repo")

    args = argparser.parse_args()

    if args.command == "resolve":
        answers = await resolve(args.question, recursive=not args.no_recurse)

        if answers:
            for a in answers:
                print(a)
        else:
            print(f"Unable to resolve {args.question}")
    elif args.command == "fetch":
        output_dir = Path(args.output_dir)
        # output_dir must not exist, or be an empty directory
        if output_dir.exists():
            if output_dir.is_file():
                print(
                    f"{output_dir} should either not exist, or be an empty directory. Is a file",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                if any(output_dir.iterdir()):
                    print(
                        f"{output_dir} should either not exist, or be an empty directory. Is a non-empty directory",
                        file=sys.stderr,
                    )
                    sys.exit(1)
        else:
            output_dir.mkdir(parents=True)

        answers = await resolve(args.question, recursive=True)
        if answers:
            last_answer = answers[-1]
            await fetch(last_answer, Path(args.output_dir))
        else:
            print(f"Unable to resolve {args.question}")


def cli_entrypoint():
    asyncio.run(main())
