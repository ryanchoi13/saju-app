"""Illustration picture + colour-layer pairs must never be mixed across deploys."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_illustration_pictures_and_layer_maps_are_revalidated():
    for name in ('m-casual-b.webp', 'm-casual-b-layers.png'):
        response = client.get('/assets/dalha-illustrations/' + name)
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-cache'
        assert response.headers.get('etag')


def test_illustration_code_is_still_never_stored():
    response = client.get('/assets/dalha-illustrations/adapter.js')
    assert response.headers['cache-control'] == 'no-store, max-age=0'
