import json
import re
import sys

import click
from ebooklib import epub

from reddit2epub.reddit2epubLib import (
    create_book_from_chapters,
    get_chapters_from_anchor,
)


def get_app_version() -> str:
    try:
        from importlib.metadata import version

        return version("reddit2epub")
    except (ImportError, LookupError):
        return "0.5.0"


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    infos = {"version": get_app_version()}
    click.echo(json.dumps(infos))
    ctx.exit(0)


@click.command()
@click.option(
    "input_url",
    "--input",
    "-i",
    required=True,
    help="The url of an arbitrary chapter of the series you want to convert",
)
@click.option(
    "output_filename",
    "--output",
    "-o",
    default="",
    help="The filename of the output epub. Defaults to the first chapter title.",
)
@click.option(
    "--overlap",
    default=2,
    help="How many common words do the titles have at the beginning.",
)
@click.option(
    "--all-reddit/--no-all-reddit",
    default=False,
    help="Search over all reddit. Meant for stories which span subreddits",
)
@click.option(
    "--version",
    help="Print version information and exit.",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
def main_cli(input_url: str, overlap: int, output_filename: str, all_reddit: bool):
    author, selected_submissions, search_title = get_chapters_from_anchor(
        input_url, overlap, all_reddit
    )

    len_subs = len(selected_submissions)
    msg = (
        f"Total number of found posts with title prefix '{search_title}' "
        f"in subreddit: {len_subs}"
    )
    print(msg)

    if len_subs == 1:
        raise RuntimeError(
            f"No other chapters found sharing the first {overlap} words "
            "with other posts from this author in this subreddit."
        )
    elif len_subs == 0:
        raise RuntimeError("No text chapters found")

    elif len_subs >= 200:
        print(
            "Got more than 200 submissions from author in this subreddit :-O. "
            "It may be possible that old chapters are not included.",
            file=sys.stderr,
        )

    # set metadata
    book_id = selected_submissions[-1].id
    book_title = selected_submissions[-1].title
    book_author = author.name

    # Build the ebook
    book = create_book_from_chapters(
        book_author, book_id, book_title, reversed(selected_submissions)
    )

    # replace all non alphanumeric chars through _ for filename sanitation
    if output_filename:
        file_name = output_filename
    else:
        file_name = (re.sub("[^0-9a-zA-Z]+", "_", book_title) + ".epub").strip("_OC")

    # write to the file
    epub.write_epub(file_name, book, {})


if __name__ == "__main__":
    main_cli()
