from app.db import normalize_database_url


def test_managed_postgres_url_uses_installed_psycopg_driver():
    assert normalize_database_url('postgres://user:secret@db.example/story') == 'postgresql+psycopg://user:secret@db.example/story'
    assert normalize_database_url('postgresql://user:secret@db.example/story') == 'postgresql+psycopg://user:secret@db.example/story'
    assert normalize_database_url('sqlite:///./storylens.db') == 'sqlite:///./storylens.db'
