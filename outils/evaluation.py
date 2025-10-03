import evaluate
from nltk.tokenize import word_tokenize
import numpy as np

rouge = evaluate.load("rouge")

from bert_score import score



def evaluation_answer(answer, reference):
    """
    Évalue la similarité entre une réponse générée et une référence.
    Args:
        answer (str): Réponse générée par le modèle.
        reference (str): Référence correcte.
    Returns:
        float: Score de similarité entre 0 et 1.
    """
    generated = list(set(word_tokenize(answer.lower())))
    references = list(set(word_tokenize(reference.lower())))

    generated = " ".join(generated)
    references = " ".join(references)
    
    rouge_result = rouge.compute(predictions=[generated], references=[references])
    rouge_result = {"Rouge1 Unigrammes": np.round(rouge_result["rouge1"], 4), "Rouge2 Bigrammes": np.round(rouge_result["rouge2"], 4)}
    
    P, R, F1 = score([generated], [reference], lang="fr")
    bert_result = {
        "Precision": np.round(P.mean().item(), 4),
        "Recall": np.round(R.mean().item(), 4),
        "F1": np.round(F1.mean().item(), 4)
    }

    print("ROUGE:", rouge_result)
    print("Bert score:", bert_result)
    return {"rouge":rouge_result, "bert_score":bert_result}
