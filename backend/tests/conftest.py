import sys
from pathlib import Path
import os
import warnings
import pytest

# Ensure the backend package directory is on sys.path for tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Silence specific deprecation warnings coming from third-party libs (pydantic/fireworks)
# This keeps test output clean; integration/upgrade should update dependencies later.
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")


@pytest.fixture(scope="session")
def fireworks_api_key():
	"""Return the FIREWORKS_API_KEY from environment if present, else None.

	Tests needing real network access should skip when this is None.
	"""
	# Prefer loading from environment variable; load_settings.py can also be used if desired
	return os.getenv("FIREWORKS_API_KEY")


# Create lightweight stubs for heavy external libraries if they're not installed.
def _ensure_stub(module_name, stub_obj):
	if module_name in sys.modules:
		return
	sys.modules[module_name] = stub_obj


class _SimpleModule(dict):
	def __getattr__(self, name):
		val = self.get(name)
		if val is None:
			# create a simple callable stub
			def _stub(*args, **kwargs):
				return None
			return _stub
		return val


try:
	import fireworks  # noqa: F401
except Exception:
	# minimal fireworks stub
	fireworks = _SimpleModule()
	class _FWClient:
		def __init__(self, api_key=None):
			self.api_key = api_key
		def __enter__(self):
			return self
		def __exit__(self, exc_type, exc, tb):
			return False
		class embeddings:
			@staticmethod
			def create(model=None, input=None):
				# mimic response.data list with .embedding
				class Item:
					def __init__(self, emb):
						self.embedding = emb
				class Resp:
					def __init__(self, data):
						self.data = data
				# return zeros for each input string
				data = [Item([0.0] * 8) for _ in (input if isinstance(input, list) else [input])]
				return Resp(data)

	fireworks.client = _SimpleModule()
	fireworks.client.Fireworks = _FWClient
	fireworks.LLM = type("LLM", (), {"__init__": lambda self, *a, **k: None, "chat": _SimpleModule()})
	_ensure_stub("fireworks", fireworks)

try:
	import importlib
	_lcts = importlib.import_module("langchain.text_splitter")
except Exception:
	# minimal text splitter
	class RecursiveCharacterTextSplitter:
		def __init__(self, chunk_size=500, chunk_overlap=50, separators=None):
			self.chunk_size = chunk_size
			self.chunk_overlap = chunk_overlap

		def split_text(self, text):
			if not text:
				return []
			chunks = []
			i = 0
			step = self.chunk_size - self.chunk_overlap
			while i < len(text):
				chunks.append(text[i:i + self.chunk_size])
				i += step
			return chunks

	langchain = _SimpleModule()
	langchain.text_splitter = _SimpleModule()
	langchain.text_splitter.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter
	_ensure_stub("langchain.text_splitter", langchain.text_splitter)
	_lcts = langchain.text_splitter

try:
	import trafilatura  # noqa: F401
except Exception:
	trafilatura = _SimpleModule()
	trafilatura.fetch_url = lambda url: "<html><body><p>stub</p></body></html>"
	_ensure_stub("trafilatura", trafilatura)

try:
	import faiss  # noqa: F401
except Exception:
	# minimal faiss stub
	faiss = _SimpleModule()
	class IndexFlatL2:
		def __init__(self, dim):
			self.dim = dim
			self._vecs = []
		def add(self, arr):
			self._vecs.extend(list(arr))
		def search(self, query, k=3):
			# return zeros and first k indices
			import numpy as _np
			idxs = _np.arange(k).reshape(1, -1)
			dists = _np.zeros_like(idxs, dtype=float)
			return dists, idxs
	faiss.IndexFlatL2 = IndexFlatL2
	_ensure_stub("faiss", faiss)

