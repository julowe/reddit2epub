import json
import re
import sys

import click
import pkg_resources
from ebooklib import epub

from reddit2epub.reddit2epubLib import (
    get_chapters_from_anchor,
    create_book_from_chapters,
)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    infos = {"version": pkg_resources.get_distribution("reddit2epub").version}
    click.echo(json.dumps(infos))
    ctx.exit()


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
    "override_title",
    "--title",
    "-t",
    default="",
    help="Title of book, overriding the default of the first chapter title.",
)
@click.option(
    "--overlap",
    default=2,
    help="How many common words do the titles have at the beginning.",
)
@click.option(
    "--max_posts",
    "-m",
    default=200,
    help="What is the maximum number of posts to fetch.",
)
@click.option(
    "--all-reddit/--no-all-reddit",
    default=False,
    help="Search over all reddit. " "Meant for stories which span subreddits",
)
@click.option(
    "--version",
    help="Print version information and exit.",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
def main_cli(
    input_url: str,
    overlap: int,
    output_filename,
    all_reddit,
    max_posts: int,
    override_title,
):
    author, selected_submissions, search_title = get_chapters_from_anchor(
        input_url, overlap, all_reddit
    )

    len_subs = len(selected_submissions)
    print(
        "Total number of found posts with title prefix '{}' in subreddit: {}".format(
            search_title, len_subs
        )
    )

    if len_subs == 1:
        raise Exception(
            "No other chapters found, which share the first {} words with other posts from this "
            "author in this subreddit.".format(overlap)
        )
    elif len_subs == 0:
        raise Exception("No text chapters found")

    elif len_subs >= max_posts:
        # TODO: make max submissions a parameter
        print(
            "Got more than {} submissions from author in this subreddit :-O. "
            "It may be possible that old chapters are not included.".format(max_posts),
            file=sys.stderr,
        )

    # set metadata
    book_id = selected_submissions[-1].id
    if not override_title:
        book_title = " ".join(
            selected_submissions[-1].title.split(" ")[0:overlap]
        )
    else:
        book_title = override_title

    book_author = author.name

    # Build the ebook
    book = create_book_from_chapters(
        book_author, book_id, book_title, reversed(selected_submissions)
    )

    # replace all non alphanumeric chars through _ for filename sanitation
    if output_filename:
        file_name = output_filename
    else:
        file_name = re.sub("[^0-9a-zA-Z]+", "_", book_title.strip(",.")) + ".epub"

    # write to the file
    epub.write_epub(file_name, book, {})


if __name__ == "__main__":
    main_cli()
