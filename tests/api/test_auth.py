import pytest

from web.base import app, database
from web.models.user import User


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
def init_database():
    # Create a test user
    user = User(
        email='user@example.com',
        name="name",
        password_hash='b305cadbb3bce54f3aa59c64fec00dea',
        salt='salt'
    )  # type: ignore
    database.session.add(user)
    database.session.commit()

    yield database

    database.session.remove()
    database.drop_all()


def test_auth_login_success(test_client, init_database):
    response = test_client.post('/api/auth/login', json={
        'email': 'user@example.com',
        'password': 'password'
    })

    data = response.get_json()
    assert response.status_code == 200
    assert 'access_token' in data


def test_auth_login_missing_fields(test_client, init_database):
    response = test_client.post('/api/auth/login', json={
        'email': 'user@example.com'
        # Missing password field
    })

    data = response.get_data(as_text=True)
    assert response.status_code == 400
    assert 'Missing fields' == data


def test_auth_login_invalid_credentials(test_client, init_database):
    response = test_client.post('/api/auth/login', json={
        'email': 'user@example.com',
        'password': 'wrong_password'
    })

    assert response.status_code == 401
    assert response.get_data(as_text=True) == 'Invalid credentials'


def test_auth_register_success(test_client, init_database):
    response = test_client.post('/api/auth/register', json={
        'email': 'user2@example.com',
        'name': "name2",
        'password': 'password2'
    })

    data = response.get_json()
    assert response.status_code == 200
    assert 'access_token' in data


def test_auth_register_missing_fields(test_client, init_database):
    response = test_client.post('/api/auth/register', json={
        'email': 'incompleteuser@example.com'
        # Missing name and password fields
    })

    data = response.get_data(as_text=True)
    assert response.status_code == 400
    assert 'Missing fields' in data


def test_auth_register_duplicate_email(test_client, init_database):
    response = test_client.post('/api/auth/register', json={
        'email': 'user@example.com',
        'name': 'Duplicate User',
        'password': 'duplicatepassword'
    })

    data = response.get_data(as_text=True)
    assert response.status_code == 400
    assert 'A user with this email already exists' in data


def test_auth_register_duplicate_username(test_client, init_database):
    response = test_client.post('/api/auth/register', json={
        'email': 'test2@example.com',
        'name': 'name',
        'password': 'duplicatepassword'
    })

    data = response.get_data(as_text=True)
    assert response.status_code == 400
    assert 'Username already taken' in data
