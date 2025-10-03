import faiss
import numpy as np

def create_faiss_index(embeddings):
    """
        crée un index FAISS pour les embeddings.
    
    Args:
        embeddings (np.ndarray): Matrice des embeddings.
    """
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index

def search_similar_documents(query, model, index, k=3):
    """
        recherche les documents similaires dans l'index FAISS.

    Args:
        query (str): La requête de l'utilisateur.
        model: Le modèle d'embeddings.
        index: L'index FAISS.
    """

    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k=k)
    return distances, indices


def search_similar_context(query, model, index, documents_indexed, sources, k=3):
    """
        Recherche le contexte pertinent pour une requête donnée.

    Args:
        query (str): La requête de l'utilisateur.   
        model: Le modèle d'embeddings.
        index: L'index FAISS.
        documents_indexed (dict): Dictionnaire avec les indices comme clés et le texte extrait comme valeurs.
        sources (list): Liste des sources correspondant aux passages.
        k (int, optional): Nombre de documents similaires à récupérer. Defaults to 3.
    """

    _, indices = search_similar_documents(query, model, index, k=k)

    indices_documents = set([sources[i] for i in indices[0]])
    context_selected = " ".join([" ".join(documents_indexed[index]) for index in indices_documents])

    return context_selected, indices_documents