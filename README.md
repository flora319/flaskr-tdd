# Flaskr-TDD

A small blogging app built with Flask using test-driven development, for ECE444 PRA6.

**Live site:** https://flaskr-tdd-550y.onrender.com (Render free tier; the first load may take ~50 seconds)

## Features

- Log in and out (username and password are `admin` / `admin`)
- Post entries while logged in
- View all entries
- Search entries by title or text (case-insensitive)
- Delete an entry by clicking it (requires login; logged-out requests get a 401)

## Stack

Flask, Flask-SQLAlchemy, Bootstrap 5, pytest, gunicorn. SQLite locally and Postgres on Render.

## Run locally

```sh
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python create_db.py
FLASK_APP=project/app.py python -m flask run -p 5001
```

Then open http://localhost:5001/.

## Tests

```sh
python -m pytest
```

The tests cover the index page, the database, login and logout, posting, search, and delete with and without login.

The tests always use a separate `test.db` SQLite file (they override `DATABASE_URL`), so they never touch the development or production database.

## Lint and format

```sh
python -m flake8 --exclude env --ignore E402,E501 .
python -m black --exclude=env .
```

## Deployment

Deployed as a Render web service (build `pip install -r requirements.txt`, start `gunicorn project.app:app`). The app reads the `DATABASE_URL` environment variable to connect to a Render Postgres database, and falls back to a local SQLite file when it is not set.
