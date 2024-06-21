from flask_jwt_extended import create_access_token
import pytest

from web.base import app, database, hasher
from web.models import User, Tag


@pytest.fixture()
def test_client():
    app.config['TESTING'] = True
    client = app.test_client()

    ctx = app.app_context()
    ctx.push()

    database.create_all()

    yield client

    database.session.remove()
    database.drop_all()
    ctx.pop()


@pytest.fixture
def user():
    u = User(
        email='user@example.com',
        name="name",
        password_hash='b305cadbb3bce54f3aa59c64fec00dea',
        salt='salt',
        tags=[Tag(tag="test", color="red")]  # type: ignore
    )  # type: ignore
    database.session.add(u)
    database.session.commit()
    return u


@pytest.fixture
def headers(user):
    access_token = create_access_token(identity=user.email)
    return {
        'Authorization': f'Bearer {access_token}'
    }


@pytest.fixture
def tag(user):
    t = Tag(user_id=user.id, tag="sample tag", color="blue")  # type: ignore
    database.session.add(t)
    database.session.commit()
    return t


def test_edit_tag_success(test_client, user, tag, headers):
    response = test_client.post('/api/tags/edit', json={
        'id': hasher.encode(tag.id),
        'tag': 'new tag name',
        'color': 'red'
    }, headers=headers)
    print(response.get_data(as_text=True))
    assert response.status_code == 200
    assert database.session.get(
        Tag, tag.id).tag == 'new tag name'  # type: ignore
    assert database.session.get(Tag, tag.id).color == 'red'  # type: ignore


def test_edit_tag_not_found(test_client, user, headers):
    response = test_client.post('/api/tags/edit', json={
        'id': hasher.encode(999),  # Non-existing tag ID
        'tag': 'new tag name',
        'color': 'red'
    }, headers=headers)
    assert response.status_code == 404
    assert response.get_data(as_text=True) == "Tag with ID 999 not found"


def test_edit_tag_user_not_authorized(test_client, user, headers):
    other_user = User(email="other@example.com", name="otheruser",
                      password_hash="hashed_password", salt="salt")  # type: ignore
    database.session.add(other_user)
    database.session.commit()
    other_tag = Tag(user_id=other_user.id, tag="other tag",
                    color="green")  # type: ignore
    database.session.add(other_tag)
    database.session.commit()

    response = test_client.post('/api/tags/edit', json={
        'id': hasher.encode(other_tag.id),
        'tag': 'new tag name',
        'color': 'red'
    }, headers=headers)
    assert response.status_code == 404
    assert response.get_data(as_text=True) == f"Tag with ID {
        other_tag.id} not found for this user"


def test_edit_tag_duplicate_name(test_client, user, tag, headers):
    another_tag = Tag(user_id=user.id, tag="another tag",
                      color="yellow")  # type: ignore
    database.session.add(another_tag)
    database.session.commit()

    response = test_client.post('/api/tags/edit', json={
        'id': hasher.encode(tag.id),
        'tag': 'another tag',  # Duplicate tag name
        'color': 'red'
    }, headers=headers)
    assert response.status_code == 400
    assert response.get_data(
        as_text=True) == "A tag with this name already exists!"
