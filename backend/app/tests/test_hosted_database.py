from sqlalchemy.engine import make_url
from app.db.session import get_async_database_url


def test_neon_url_preserves_credentials_and_enables_tls():
    url = get_async_database_url('postgresql://user:p%40ss@db.example/app?sslmode=require&channel_binding=require')
    parsed = make_url(url)
    assert parsed.drivername == 'postgresql+asyncpg'
    assert parsed.password == 'p@ss'
    assert parsed.query == {'ssl': 'require'}


def test_existing_async_url_unchanged():
    url = 'postgresql+asyncpg://user:pass@localhost/app'
    assert get_async_database_url(url) == url
