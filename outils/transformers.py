import spacy


def split_text_into_paragraphs_spacy(texts):
    """ Découpe un texte en paragraphes en utilisant spaCy pour la segmentation.
    """

    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        from spacy.cli import download
        download("fr_core_news_sm")
        nlp = spacy.load("fr_core_news_sm")

    spacy.util.fix_random_seed()
    nlp = spacy.load("fr_core_news_sm")
    nlp.max_length = len(texts) + 1000

    s = texts.replace('\n', ' ')
    docs = nlp(texts)
    return [sent.text for sent in docs.sents]

def textTosentences(texts):
    """ Découpe les textes en phrases en utilisant spaCy pour la segmentation.

    Args:
        texts (dict): Dictionnaire avec les URLs comme clés et les textes comme valeurs.
    """

    texts_transformed = {}
    for url in texts.keys():
        print(f"Processing {url}...")
        texts_transformed[url] = split_text_into_paragraphs_spacy(texts[url])

    return texts_transformed