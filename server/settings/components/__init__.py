from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR.joinpath('some')
# `pathlib` is better than writing: dirname(dirname(dirname(__file__)))
BASE_DIR = Path(__file__).parent.parent.parent.parent

# Loading `.env` files
# See docs: https://github.com/joke2k/django-environ
env = environ.Env()
environ.Env.read_env(BASE_DIR.joinpath("config", ".env").as_posix())
