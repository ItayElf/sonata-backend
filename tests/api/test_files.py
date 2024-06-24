import io
from flask_jwt_extended import create_access_token
import pytest
from web.base import app, database, hasher
from web.models import Piece, User, Tag


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


def test_upload_link_file_success(test_client, piece, headers):
    response = test_client.post('/api/files/upload_link', json={
        "id": hasher.encode(piece.id),
        "link": "http://example.com",
    }, headers=headers)
    assert response.status_code == 200
    assert database.session.get(
        Piece, piece.id).file_type == 'http://example.com'  # type: ignore
    assert "file_type" in response.json


def test_upload_link_file_not_found(test_client, headers):
    response = test_client.post('/api/files/upload_link', json={
        "id": hasher.encode(999),
        "link": "http://example.com",
    }, headers=headers)
    assert response.status_code == 404
    assert response.get_data(as_text=True) == "Piece with ID 999 not found"


def test_upload_link_file_unauthorized(test_client, piece):
    other_user = User(email="other@example.com", name="otheruser",
                      password_hash="hashed_password", salt="salt")  # type: ignore
    database.session.add(other_user)
    database.session.commit()

    access_token = create_access_token(identity=other_user.email)
    response = test_client.post('/api/files/upload_link', json={
        "id": hasher.encode(piece.id),
        "link": "http://example.com",
    }, headers={
        'Authorization': f'Bearer {access_token}'
    })
    assert response.status_code == 404
    assert response.get_data(as_text=True) == f"Piece with ID {
        piece.id} not found for this user"


def test_files_upload_file_success(test_client, headers, piece):
    data = {
        "id": hasher.encode(piece.id)
    }
    file_data = {
        'file': (io.BytesIO(b"some initial text data"), "test.txt")
    }
    response = test_client.post(
        '/api/files/upload_file',
        headers=headers,
        data={**data, **file_data},
    )
    assert response.status_code == 200
    assert database.session.get(
        Piece, piece.id).file_type == 'text/plain'  # type: ignore
    assert database.session.get(
        Piece, piece.id).file_id is not None  # type: ignore


def test_files_upload_file_missing_file(test_client, headers, piece):
    data = {
        "id": hasher.encode(piece.id)
    }
    response = test_client.post(
        '/api/files/upload_file',
        headers=headers,
        data={**data},
    )
    assert response.status_code == 400


def test_files_upload_file_too_large(test_client, headers, piece):
    file_size = (30*1024*1024+1)
    data = {
        "id": hasher.encode(piece.id)
    }
    file_data = {
        'file': (io.BytesIO(b"A" * file_size), "test.txt")
    }
    response = test_client.post(
        '/api/files/upload_file',
        headers=headers,
        data={**data, **file_data},
    )
    assert response.status_code == 400
    assert response.get_data(
        as_text=True) == f"File too large! ({file_size / 1024 / 1024}MB > 30MB)"


def test_files_upload_file_file_unauthorized(test_client, piece):
    other_user = User(email="other@example.com", name="otheruser",
                      password_hash="hashed_password", salt="salt")  # type: ignore
    database.session.add(other_user)
    database.session.commit()

    access_token = create_access_token(identity=other_user.email)
    data = {
        "id": hasher.encode(piece.id)
    }
    file_data = {
        'file': (io.BytesIO(b"some initial text data"), "test.txt")
    }
    response = test_client.post(
        '/api/files/upload_file',
        headers={'Authorization': f'Bearer {access_token}'},
        data={**data, **file_data},
    )
    assert response.status_code == 404
    assert response.get_data(as_text=True) == f"Piece with ID {
        piece.id} not found for this user"
