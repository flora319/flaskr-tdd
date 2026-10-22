import json
import os
import pytest
from pathlib import Path

TEST_DB = "test.db"
BASE_DIR = Path(__file__).resolve().parent.parent

# Point the app at the test database before it is imported, so the tests
# never touch the real (local or Render Postgres) database.
os.environ["DATABASE_URL"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

from project.app import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()  # setup
        yield app.test_client()  # tests run here
        db.drop_all()  # teardown


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """initial test. ensure that the database exists"""
    tester = BASE_DIR.joinpath(TEST_DB).is_file()
    assert tester


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data


def test_search_page_loads(client):
    """Ensure the search page loads with no query"""
    rv = client.get("/search/")
    assert rv.status_code == 200
    assert b"Search:" in rv.data


def test_search_finds_matching_posts(client):
    """Ensure search matches title or text, ignoring case"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post(
        "/add",
        data=dict(title="Apple pie", text="Baked fresh"),
        follow_redirects=True,
    )
    client.post(
        "/add",
        data=dict(title="Banana bread", text="Contains APPLE sauce"),
        follow_redirects=True,
    )
    client.post(
        "/add",
        data=dict(title="Cherry tart", text="No fruit overlap"),
        follow_redirects=True,
    )

    rv = client.get("/search/?query=apple")
    assert rv.status_code == 200
    assert b"Apple pie" in rv.data  # matched on title
    assert b"Banana bread" in rv.data  # matched on text, different case
    assert b"Cherry tart" not in rv.data


def test_search_no_results(client):
    """Ensure a query that matches nothing shows no posts"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post(
        "/add",
        data=dict(title="Apple pie", text="Baked fresh"),
        follow_redirects=True,
    )

    rv = client.get("/search/?query=zzzz")
    assert rv.status_code == 200
    assert b"Apple pie" not in rv.data


def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 1


def test_delete_requires_login(client):
    """Ensure a logged-out user gets a 401 and the post is not deleted"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post(
        "/add",
        data=dict(title="Keep me", text="Do not delete"),
        follow_redirects=True,
    )
    logout(client)

    rv = client.get("/delete/1")
    assert rv.status_code == 401
    assert json.loads(rv.data)["message"] == "Please log in."

    rv = client.get("/")
    assert b"Keep me" in rv.data


def test_delete_works_when_logged_in(client):
    """Ensure a logged-in user can delete a post"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post(
        "/add",
        data=dict(title="Delete me", text="Going away"),
        follow_redirects=True,
    )

    rv = client.get("/delete/1")
    assert rv.status_code == 200
    assert json.loads(rv.data)["status"] == 1

    rv = client.get("/")
    assert b"Delete me" not in rv.data
