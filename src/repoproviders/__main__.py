import argparse
import asyncio

from .resolvers import resolve


async def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("question", help="What should we try to resolve?")
    argparser.add_argument(
        "--no-recurse",
        help="Do not recurse, return after first answer",
        action="store_true",
    )
    args = argparser.parse_args()

    answers = await resolve(args.question, recursive=not args.no_recurse)

    if answers:
        for a in answers:
            print(a)
    else:
        print(f"Unable to resolve {args.question}")


def cli_entrypoint():
    asyncio.run(main())
