import evaluate
from nltk.tokenize import word_tokenize
import numpy as np
from bert_score import score


class Evaluation:
    def __init__(self):
        self.rouge = evaluate.load("rouge")


    def evaluation_answer(self, answer, reference):
        """Evaluate the similarity between a generated answer and a reference.

        This function uses ROUGE (unigram and bigram) and BERTScore 
        to assess the similarity between the generated answer and the reference text.

        Args:
            answer (str): The generated answer from the model.
            reference (str): The correct reference answer.

        Returns:
            dict: A dictionary containing:
                - "rouge" (dict): ROUGE scores with keys 
                "Rouge1 Unigrams" and "Rouge2 Bigrams".
                - "bert_score" (dict): BERTScore metrics with keys 
                "Precision", "Recall", and "F1".
        """
        generated = list(set(word_tokenize(answer.lower())))
        references = list(set(word_tokenize(reference.lower())))

        generated = " ".join(generated)
        references = " ".join(references)
        
        rouge_result = self.rouge.compute(predictions=[generated], references=[references])
        rouge_result = {
            "Rouge1 Unigrammes": np.round(rouge_result["rouge1"], 4), 
            "Rouge2 Bigrammes": np.round(rouge_result["rouge2"], 4)
        }
        
        P, R, F1 = score([generated], [reference], lang="fr")
        bert_result = {
            "Precision": np.round(P.mean().item(), 4),
            "Recall": np.round(R.mean().item(), 4),
            "F1": np.round(F1.mean().item(), 4)
        }
        return {"rouge": rouge_result, "bert_score": bert_result}