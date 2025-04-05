# Reddit to epub converter

This little script allows you to convert reddit stories which are published in
multiple posts to one single epub file.

## Usage

~~Install via `pip install reddit2epub`.
It provides the cli at the command `reddit2epub --help`.~~

While under development install by cloning this repo,
cd into the repo and then running:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --editable .
```

Then rename `env-dist` to `.env` and edit it with your reddit credentials.
TODO: Add how to do this. I forget what I did.
[PRAW's Docs](https://praw.readthedocs.io/en/stable/getting_started/authentication.template)
point you to [Old Reddit Apps](https://old.reddit.com/prefs/apps/)
so that is probably what I did.

You should then be able to run `reddit2epub --overlap X -i LINK`
where `X` is the number of words that overlap in the title of all the posts
you want to collect, and `LINK` is the link to a post/story in the series that
you want to collect.

## Admin To Dos

- [ ] make pull request against original repo
      (to get author support, or at least let people see the updates)
- [ ] make pull request or split to new project?
- [ ] Guide of how to create needed creds with reddit account
- [ ] how to edit .env-dist template file to .env
- [ ] how to run code, with example

## Code To Dos

- [x] parse command line args before authenticating user
      (e.g. `reddit2epub --help` will auth and then print help...)
- [ ] add short args (e.g. `-h` for `--help)
- [ ] more feedback
  - [ ] output when epub is saved and what filename

## Features to add

- [ ] Output list of chapters/urls so user can edit them
      (why? so when author changes from "The Blah story" to "Blah Story",
      you can cat them together, or if there are odd one-offs to include in a
      specific order)
- [ ] Download comments (all, only OP's, only threads with OP in them)
