import os
os.environ['DATABASE_URL'] = 'sqlite://'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app, Base, User, get_db, password_hasher

engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)

def db_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_db] = db_override
client = TestClient(app)

def test_registration_and_duplicate():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    payload = {'name': ' Danial Awan ', 'email': 'DANIAL@example.com',
               'phone': '03001234567', 'password': 'Example123'}
    response = client.post('/api/register', json=payload)
    assert response.status_code == 201
    assert response.json()['name'] == 'Danial Awan'
    assert response.json()['email'] == 'danial@example.com'
    assert 'password_hash' not in response.json()
    with Session(engine) as db:
        user = db.scalar(select(User))
        assert user.password_hash != payload['password']
        assert password_hasher.verify(payload['password'], user.password_hash)
    assert client.post('/api/register', json=payload).status_code == 409

def test_invalid_fields_never_save():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    valid = {'name': 'Danial', 'email': 'danial@example.com',
             'phone': '03001234567', 'password': 'Example123'}
    for field, value in [('name', ' '), ('email', 'wrong'), ('phone', '123'),
                         ('password', 'abcdefgh'), ('password', 'x1')]:
        assert client.post('/api/register', json={**valid, field: value}).status_code == 422
    assert client.post('/api/register', json={**valid, 'role': 'admin'}).status_code == 422
    with Session(engine) as db:
        assert db.scalar(select(User)) is None
