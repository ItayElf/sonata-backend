from flask_jwt_extended import create_access_token
import pytest
from web.base import app, database, hasher
from web.models import User, Tag
from web.models.piece import Piece


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
def tags(user):
    t1 = Tag(user_id=user.id, tag="sample tag", color="blue")  # type: ignore
    t2 = Tag(user_id=user.id, tag="sample tag2", color="red")  # type: ignore
    database.session.add(t1)
    database.session.add(t2)
    database.session.commit()
    return t1, t2


@pytest.fixture
def piece(user, tags):
    p = Piece(name="test", description="test", instrument="Piano",
              state=1, tags=list(tags), user_id=user.id)  # type: ignore
    database.session.add(p)
    database.session.commit()
    return p


def test_edit_piece_success(test_client, user, headers, tags, piece):
    response = test_client.post('/api/pieces/edit', json={
        "id": hasher.encode(piece.id),
        "name": "new_name",
        "description": "test description",
        "instrument": None,
        "state": 2,
        "tag_ids": [hasher.encode(tags[0].id)]
    }, headers=headers)
    assert response.status_code == 200
    assert database.session.get(
        Piece, piece.id).name == 'new_name'  # type: ignore
    assert database.session.get(
        Piece, piece.id).instrument is None  # type: ignore
    assert len(database.session.get(
        Piece, piece.id).tags) == 1  # type: ignore
    assert "tags" in response.json
    assert "file_id" in response.json


def test_edit_piece_not_found(test_client, user, headers, tags):
    response = test_client.post('/api/pieces/edit', json={
        "id": hasher.encode(999),
        "name": "new_name",
        "description": "test description",
        "instrument": None,
        "state": 2,
        "tag_ids": [hasher.encode(tags[0].id)]
    }, headers=headers)
    assert response.status_code == 404
    assert response.get_data(as_text=True) == "Piece with ID 999 not found"


def test_edit_piece_unauthorized(test_client, user, headers, tags, piece):
    other_user = User(email="other@example.com", name="otheruser",
                      password_hash="hashed_password", salt="salt")  # type: ignore
    database.session.add(other_user)
    database.session.commit()
    other_tag = Tag(user_id=other_user.id, tag="other tag",
                    color="green")  # type: ignore
    database.session.add(other_tag)
    database.session.commit()
    access_token = create_access_token(identity=other_user.email)

    response = test_client.post('/api/pieces/edit', json={
        "id": hasher.encode(piece.id),
        "name": "new_name",
        "description": "test description",
        "instrument": None,
        "state": 2,
        "tag_ids": [hasher.encode(other_tag.id)]
    }, headers={
        'Authorization': f'Bearer {access_token}'
    })
    assert response.status_code == 404
    assert response.get_data(as_text=True) == f"Piece with ID {
        piece.id} not found for this user"


def test_edit_piece_duplicate(test_client, user, piece, headers, tags):
    another_piece = Piece(name="test2", description="test", instrument="Piano2",
                          # type: ignore
                          state=1, tags=list(tags), user_id=user.id)
    database.session.add(another_piece)
    database.session.commit()
    response = test_client.post('/api/pieces/edit', json={
        "id": hasher.encode(piece.id),
        "name": another_piece.name,
        "description": "test description",
        "instrument": another_piece.instrument,
        "state": 2,
        "tag_ids": [hasher.encode(tags[0].id)]
    }, headers=headers)

    assert response.status_code == 400
    assert response.get_data(
        as_text=True) == "A piece with this name already exists for this instrument!"


def test_add_piece_success(test_client, user, headers, tags):
    response = test_client.post('/api/pieces/add', json={
        "name": "name",
        "description": None,
        "instrument": None,
        "state": 1,
        "tag_ids": [hasher.encode(tag.id) for tag in tags]
    }, headers=headers)
    assert response.status_code == 200
    p = Piece.query.filter_by(name="name").first()
    assert p is not None
    assert p.instrument is None
    assert len(p.tags) == 2
    assert response.json["tags"][0]["tag"] == tags[0].tag


def test_add_piece_duplicate(test_client, user, headers, tags, piece):
    response = test_client.post('/api/pieces/add', json={
        "name": piece.name,
        "description": None,
        "instrument": piece.instrument,
        "state": 1,
        "tag_ids": [hasher.encode(tag.id) for tag in tags]
    }, headers=headers)
    assert response.status_code == 400
    assert response.get_data(
        as_text=True) == "A piece with this name already exists for this instrument!"
