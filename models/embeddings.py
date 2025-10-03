from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk


def create_index_for_documents(documents):
    """ Crée un index pour les documents.

    Args:
        documents (dict): Dictionnaire avec les URLs comme clés et le texte extrait comme valeurs.
    """

    documents_indexed = {}
    indexed_to_url = {}

    for i, url in enumerate(documents):
        documents_indexed[i] = documents[url]
        indexed_to_url[i] = url
    
    return documents_indexed, indexed_to_url    

def chunking(documents):
    """
        Divise les documents en passages plus petits. Et retourne les passages et leurs sources. 
    """

    chunks = []
    sources = []
    for doc_name, passages in documents.items():
        for passage in passages:
            chunks.append(passage)
            sources.append(doc_name)
    
    return chunks, sources

def create_embeddings(chunks, model_name):
    """
        crée des embeddings pour les passages.
    """
    
    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks)
    return model, embeddings

def context_embeddings(chunks, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    """
        crée des embeddings pour les contextes.

    Args:
        documents (dict): Dictionnaire avec les URLs comme clés et le texte extrait comme valeurs.
        model_name (str, optional): Nom du modèle d'embeddings. Defaults to "paraphrase-multilingual-MiniLM-L12-v2".
    """
     
    model, embeddings = create_embeddings(chunks, model_name=model_name)

    return model, embeddings, chunks

def create_chunks_and_index(documents):
    """
        Crée des passages et un index pour les documents.

    Args:
        documents (dict): Dictionnaire avec les URLs comme clés et le texte extrait comme valeurs.
    """

    documents_indexed, indexed_to_url = create_index_for_documents(documents)
    chunks, sources = chunking(documents_indexed)

    return chunks, sources, indexed_to_url, documents_indexed

nltk.download('punkt_tab')

def tokenize_text(text):
    """
    Tokenise un texte en phrases puis chaque phrase en mots.
    Args:
        text (str): Texte à tokeniser.
    Returns:
        list of list of str: Liste de phrases, chaque phrase étant une liste de mots.
    """
    sentences = sent_tokenize(text)
    return [word_tokenize(sentence) for sentence in sentences]