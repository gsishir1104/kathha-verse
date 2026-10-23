from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from app.static_frontend import StaticExportFiles


def test_exported_pages_and_existing_paths(tmp_path):
    (tmp_path / 'index.html').write_text('home')
    (tmp_path / 'for-writers.html').write_text('writers')
    (tmp_path / 'guides').mkdir()
    (tmp_path / 'guides' / 'how-to-find-beta-readers.html').write_text('guide')
    (tmp_path / 'reset-password.html').write_text('reset')
    (tmp_path / '404.html').write_text('not found')
    (tmp_path / 'site.css').write_text('body {}')
    (tmp_path / 'api').mkdir()
    (tmp_path / 'api' / 'missing.html').write_text('not an API')
    app = Starlette(routes=[Mount('/', app=StaticExportFiles(directory=tmp_path, html=True))])
    with TestClient(app) as client:
        for path, content in [('/', 'home'), ('/for-writers', 'writers'), ('/guides/how-to-find-beta-readers', 'guide'), ('/reset-password.html', 'reset'), ('/site.css', 'body {}')]:
            response = client.get(path)
            assert response.status_code == 200
            assert response.text == content
        for path in ['/missing', '/api/missing', '/missing.js']:
            assert client.get(path).status_code == 404
        assert client.post('/for-writers').status_code == 405


def test_export_without_a_custom_error_page(tmp_path):
    (tmp_path / 'for-writers.html').write_text('writers')
    app = Starlette(routes=[Mount('/', app=StaticExportFiles(directory=tmp_path, html=True))])
    with TestClient(app) as client:
        assert client.get('/for-writers').status_code == 200
        assert client.get('/missing').status_code == 404
