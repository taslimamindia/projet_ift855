from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

from outils.dataset import Data


class Embeddings:
    def __init__(self, data:Data):
        self.data = data
        nltk.download('punkt_tab')

    def chunking(self):
        """Split the documents into smaller passages.
        """

        self.data.chunks = []
        self.data.sources = []
        for doc_name, passages in self.data.documents.items():
            for passage in passages:
                self.data.chunks.append(passage)
                self.data.sources.append(doc_name)

    def context_embeddings(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        """Create embeddings for contexts.

        Args:
            model_name (str, optional): Embedding model name. 
                Defaults to "paraphrase-multilingual-MiniLM-L12-v2".
        """

        self.data.model = SentenceTransformer(model_name)
        self.data.embeddings = self.data.model.encode(self.data.chunks)

    def tokenize_text(self, text):
        """Tokenize a text into sentences, then each sentence into words.

        Args:
            text (str): Input text to tokenize.

        Returns:
            list of list of str: A list of sentences, where each sentence is represented 
            as a list of tokenized words.
        """
        sentences = sent_tokenize(text)
        return [word_tokenize(sentence) for sentence in sentences]