"""Assert both AI entry points send credentials only to the selected provider."""
import asyncio
import json
import httpx
from pydantic import SecretStr
from app.config import Settings, settings
from app.services.screener import parser, cache
from app.schemas.screener import ParsedScreen
from app.tests.test_stock_analysis import agent, report, SELECTION, stream_response


def test_nebius_selected_without_revealing_key(monkeypatch):
    monkeypatch.setenv('NEBIUS_API_KEY', 'test-nebius-secret')
    config = Settings(_env_file=None, DEBUG=False)
    assert config.ai_provider == 'Nebius'
    assert config.ai_model == config.screener_model == 'nvidia/nemotron-3-super-120b-a12b'
    assert 'test-nebius-secret' not in repr(config)
    config.NEBIUS_API_KEY = None
    assert config.ai_provider == 'NVIDIA'


def test_both_clients_use_nebius_key_model_and_endpoint(monkeypatch):
    monkeypatch.setattr(settings, 'NEBIUS_API_KEY', SecretStr('isolated-nebius-key'))
    monkeypatch.setattr(settings, 'NVIDIA_API_KEY', SecretStr('must-not-send'))
    monkeypatch.setattr(settings, 'NEBIUS_BASE_URL', 'https://api.tokenfactory.us-central1.nebius.com/v1/')
    monkeypatch.setattr(settings, 'NEBIUS_MODEL', 'nvidia/nemotron-3-super-120b-a12b')
    draft = ParsedScreen(market='US', filters=[])
    calls = []
    def provider(request):
        assert str(request.url) == settings.ai_base_url + 'chat/completions'
        assert request.headers['Authorization'] == 'Bearer isolated-nebius-key'
        body = json.loads(request.content)
        assert body['model'] == settings.NEBIUS_MODEL
        calls.append(body)
        return stream_response(draft.model_dump_json() if len(calls) == 1 else json.dumps(SELECTION))
    for module in (parser, agent):
        monkeypatch.setattr(module, 'DefaultAsyncHttpxClient', lambda **kwargs: httpx.AsyncClient(transport=httpx.MockTransport(provider), **kwargs))
    async def miss(*args):
        return None
    monkeypatch.setattr(cache, 'get', miss)
    monkeypatch.setattr(cache, 'put', miss)
    assert asyncio.run(parser.parse_query('All US companies')) == draft
    assert asyncio.run(agent._nvidia_research({}, report().evidence)).summary
    assert len(calls) == 2
