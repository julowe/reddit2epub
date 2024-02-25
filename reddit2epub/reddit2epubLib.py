from typing import List, Iterable

from dotenv import dotenv_values
import pkg_resources
import praw
from ebooklib import epub
from ebooklib.epub import EpubBook
from praw.reddit import Redditor, Submission, Subreddit
import sys

storedAPIcreds = dotenv_values(".env")

# Failure modes to check here: files don't exist, .env.dist has non-template credentials instead of .env file


# check that .env was loaded correctly
if not storedAPIcreds:
    # .env file not loaded or found, so let's check if .env.dist exists
    templateAPIcreds = dotenv_values(".env.dist")
    if not templateAPIcreds:
        # .env.dist file not loaded or found either
        raise Exception(
            "Could not load .env or .env.dist file. "
            "Please check README.md file for instructions on how to add credentials to .env"
        )
    # check if .env.dist has any template values
    elif (
        templateAPIcreds["reddit_id"] == "Replace_Me"
        and templateAPIcreds["reddit_secret"] == "Replace_Me_Too"
    ):
        raise Exception(
            "Could not load .env file. "
            "And found template values in .env.dist file. "
            "Please check README.md file for instructions on how to add credentials to .env"
        )
    # could not load .env file and .env.dist has non-template values (instead of .env having them)
    else:
        raise Exception(
            "Found updated values in .env.dist file but no .env file. "
            "Please check README.md file for instructions on how to add credentials to .env"
        )

if not storedAPIcreds["reddit_id"]:
    raise Exception("No reddit_id found. Please add it to .env")
if not storedAPIcreds["reddit_secret"]:
    raise Exception("No reddit_secret found. Please add it to .env")

if not storedAPIcreds["reddit_username"] or not storedAPIcreds["reddit_password"]:
    reddit = praw.Reddit(
        client_id=storedAPIcreds["reddit_id"],
        client_secret=storedAPIcreds["reddit_secret"],
        user_agent="pc:Reddit stories to epub:v{} (by u/jklideas and mircohaug)".format(
            pkg_resources.get_distribution("reddit2epub").version
        ),
    )
else:
    print("Authenticating to Reddit API with stored username and password...")
    reddit = praw.Reddit(
        client_id=storedAPIcreds["reddit_id"],
        client_secret=storedAPIcreds["reddit_secret"],
        user_agent="pc:Reddit stories to epub:v{} (by u/jklideas and mircohaug)".format(
            pkg_resources.get_distribution("reddit2epub").version
        ),
        username=storedAPIcreds["reddit_username"],
        password=storedAPIcreds["reddit_password"],
    )

try:
    reddit.user.me()
except Exception as e:
    if e.error == "invalid_grant":
        print("Authentication failed. Please check your credentials in .env")
        sys.exit(1)
    else:
        raise
else:
    print("Authenticated successfully.")


def get_chapters_from_anchor(
    input_url,
    overlap: int = 2,
    all_reddit: bool = False,
) -> (Redditor, List[Submission], str):
    author, post_subreddit, title = process_anchor_url(input_url)

    search_title = " ".join(title.split(" ")[:overlap])

    selected_submissions = get_selected_posts(
        author=author,
        post_subreddit=post_subreddit,
        all_reddit=all_reddit,
        search_title=search_title,
    )
    return author, selected_submissions, search_title


def create_book_from_chapters(
    book_author: str,
    book_id: str,
    book_title: str,
    reddit_chapters: Iterable[Submission],
) -> EpubBook:
    book = epub.EpubBook()
    book.set_identifier(book_id)
    book.set_title(book_title)
    book.add_author(book_author)
    book.set_language("en")
    cover = epub.EpubHtml(title=book_title, file_name="cover.xhtml", lang="en")
    cover.content = (
        "<div><h1>{0}</h1>"
        '<h2><a href="https://www.reddit.com/user/{1}">{1}</a></h2>'
        "{2}</div>".format(
            book_title, book_author, "Created with the reddit2epub python package"
        )
    )
    book.add_item(cover)
    book_chapters = []
    # check for title prefix
    for i, sub in enumerate(reddit_chapters):
        # create chapter
        c1 = epub.EpubHtml(
            title=sub.title, file_name="chap_{}.xhtml".format(i), lang="en"
        )
        c1.content = """<h1>{0}</h1>
                     <a href="{1}">Original</a>
                     {2}
                     <a href="{1}">Original</a>
                     """.format(
            sub.title, sub.shortlink, sub.selftext_html
        )

        # add chapter
        book.add_item(c1)
        book_chapters.append(c1)

    # define Table Of Contents
    book.toc = book_chapters
    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    # basic spine
    spine = [cover, "nav"]
    spine.extend(book_chapters)
    # is used to generate the toc at the start
    book.spine = spine
    return book


def get_selected_posts(
    author: Redditor,
    post_subreddit: Subreddit,
    search_title: str,
    all_reddit: bool = False,
) -> List[Submission]:
    if all_reddit:
        sub_to_search_in = reddit.subreddit("all")
    else:
        sub_to_search_in = post_subreddit
    # is limited to 250 items
    list_of_posts = sub_to_search_in.search(
        'author:"{}" title:"{}" '.format(author, search_title), limit=None, sort="new"
    )
    list_of_posts = list(list_of_posts)
    selected_submissions = []
    for p in list_of_posts:
        # starting with the same words
        if p.title.lower().startswith(search_title.lower()) and isinstance(
            p, Submission
        ):
            if p.is_self:
                selected_submissions.append(p)
            else:
                # is crosspost if not likely media and ignored
                if hasattr(p, "crosspost_parent"):
                    original_post = list(reddit.info(fullnames=[p.crosspost_parent]))[0]
                    if not original_post.is_self:
                        # double crossposts not supported
                        continue
                    else:
                        if isinstance(original_post, Submission):
                            selected_submissions.append(original_post)
    return selected_submissions


def process_anchor_url(input_url: str) -> (Redditor, Subreddit, str):
    initial_submission = reddit.submission(url=input_url)
    title = initial_submission.title
    author = initial_submission.author
    post_subreddit = initial_submission.subreddit
    return author, post_subreddit, title
