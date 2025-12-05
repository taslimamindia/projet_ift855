from types import SimpleNamespace
from models.LLM import Fireworks_LLM


# Fake minimal LLM to avoid network calls during tests
class FakeLLM:
    def __init__(self, *args, **kwargs):
        # provide a minimal chat interface used by the real class
        class _Chat:
            class completions:
                @staticmethod
                def create(*a, **k):
                    # return a structure compatible with usage in the code
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=""))])

        self.chat = _Chat()


def test_detect_language_empty_returns_none(monkeypatch):
    # Patch the LLM used in models.LLM to avoid real Fireworks initialization
    monkeypatch.setattr("models.LLM.LLM", FakeLLM)

    data = SimpleNamespace(fireworks_api_key="test-api-key")
    fw = Fireworks_LLM(data)
    assert fw.detect_language("") is None


def test_detect_language_monkeypatched(monkeypatch):
    # Patch the LLM used in models.LLM to avoid real Fireworks initialization
    monkeypatch.setattr("models.LLM.LLM", FakeLLM)

    data = SimpleNamespace(fireworks_api_key="test-api-key")
    fw = Fireworks_LLM(data)

    # Monkeypatch langid.classify and pycountry.languages.get
    def fake_classify(text):
        return ("fr", 0.99)

    def fake_get(alpha_2):
        return SimpleNamespace(name="French")

    monkeypatch.setattr("models.LLM.langid.classify", fake_classify)
    monkeypatch.setattr("models.LLM.pycountry.languages.get", fake_get)

    lang = fw.detect_language("Bonjour tout le monde")
    assert lang == "French"
