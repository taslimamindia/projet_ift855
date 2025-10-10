import evaluate
from nltk.tokenize import word_tokenize
import numpy as np
from bert_score import score
import matplotlib.pyplot as plt
import pandas as pd
from fireworks import LLM
import json
from .dataset import Data
import re


class Evaluation:
    def __init__(self, data:Data):
        self.rouge = evaluate.load("rouge")
        self.data = data


    def create_df(self, results):
        """
        Create a formatted pandas DataFrame from evaluation results.

        This method transforms a list of evaluation result dictionaries (typically containing
        ROUGE and BERTScore metrics) into a structured DataFrame with multi-level column headers.

        Args:
            results (list[dict]): A list of dictionaries where each element contains:
                - "rouge": dict with keys "Rouge1 Unigrammes" and "Rouge2 Bigrammes"
                - "bert_score": dict with keys "Precision", "Recall", and "F1"

        Returns:
            pandas.DataFrame: A DataFrame with multi-index columns for metric categories 
            ("Rouge", "BERT Score") and test-level rows labeled as "Test 1", "Test 2", etc.
        """

        rows = []
        for i, r in enumerate(results, start=1):
            row = {
                ("Rouge", "Rouge1 Unigrammes"): r["rouge"]["Rouge1 Unigrammes"],
                ("Rouge", "Rouge2 Bigrammes"): r["rouge"]["Rouge2 Bigrammes"],
                ("BERT Score", "Precision"): r["bert_score"]["Precision"],
                ("BERT Score", "Recall"): r["bert_score"]["Recall"],
                ("BERT Score", "F1"): r["bert_score"]["F1"],
            }
            rows.append(row)

        df_scores = pd.DataFrame(rows)
        df_scores.index = [f"Test {i}" for i in range(1, len(df_scores)+1)]
        return df_scores
    

    def print_results(self, df_scores):
        return df_scores.style.set_properties(**{'text-align': 'center'})


    def plot_figure(self, df):
        """
        Plot the evolution of evaluation metrics across tests.

        This method generates a line plot for each metric in the provided DataFrame, 
        showing how scores evolve across multiple test cases. It automatically handles 
        both single-level and multi-level column names.

        Args:
            df (pandas.DataFrame): DataFrame containing evaluation scores, where rows 
                represent tests and columns represent metrics (e.g., ROUGE, BERTScore).

        Returns:
            None: Displays the plot using matplotlib.
        """

        plt.figure(figsize=(14,6))

        x = df.index.astype(str)

        for col in df.columns:
            if isinstance(col, str):
                col_str = col
            else:
                col_str = ", ".join(col)
            
            plt.plot(x, df[col], marker="o", label=col_str)

        plt.ylim(0, 1) 
        plt.xlabel("Tests")
        plt.ylabel("Scores")
        plt.title("Évolution des métriques par test")
        plt.legend()
        plt.grid(True)
        plt.show()


    def plot_bar(self, df, metrics):
        """
        Plot a grouped bar chart comparing metrics for two modes: with and without context.

        This method visualizes the difference in performance metrics (e.g., ROUGE, BERTScore)
        between "With context" and "Without context" evaluation modes across multiple tests.

        Args:
            df (pandas.DataFrame): DataFrame containing evaluation results. Must include:
                - a "mode" column with values "With context" and "Without context"
                - one column per metric listed in `metrics`
            metrics (list[str]): List of metric names to plot (each corresponding to a column in `df`).

        Returns:
            None: Displays a matplotlib figure with 2×2 subplots of grouped bar charts.
        """

        n_tests = len(df) // 2

        fig, axes = plt.subplots(2, 2, figsize=(15, 8), sharey=True)
        width = 0.35
        x = np.arange(n_tests)
        with_context = "With context"
        without_context = "Without context"
        colors = {without_context: "tomato", with_context: "mediumseagreen"}
        axes = [ax for axe in axes for ax in axe]

        for i, metric in enumerate(metrics):
            ax = axes[i]
            values_without = df[df["mode"] == without_context][metric].values
            values_with = df[df["mode"] == with_context][metric].values
            ax.bar(x - width/2, values_without, width, label=without_context, color=colors[without_context])
            ax.bar(x + width/2, values_with, width, label=with_context, color=colors[with_context])
            ax.set_title(metric.capitalize(), fontsize=12, fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels([f"Test {i+1}" for i in range(n_tests)])
            ax.set_ylim(0, 1.1)
            ax.set_ylabel("Score")
            ax.grid(axis="y", linestyle="--", alpha=0.4)

        axes[0].legend(loc="upper left", bbox_to_anchor=(0, 1.15))
        fig.suptitle("RAG Evaluation: With vs Without Context", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.show()


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


    def evaluate_rag_with_fireworks_g_eval(
        self,
        dataset,
        llm_model_name="accounts/fireworks/models/gpt-oss-20b",
        strict_mode=True
    ):
        """
        Évalue un système RAG avec et sans contexte en utilisant G-Eval via Fireworks.

        Args:
            dataset (list[dict]): liste de dictionnaires contenant :
                {
                    "question": str,
                    "expected_answer": str,
                    "context": str,
                    "answer_no_context": str,
                    "answer_with_context": str
                }
            llm_model_name (str): modèle juge Fireworks à utiliser.
            strict_mode (bool): si True, encourage des scores discrets (0 ou 1).

        Returns:
            pd.DataFrame : un tableau contenant les scores et justifications.
        """
        
        fw = LLM(api_key=self.data.fireworks_api_key, model=llm_model_name, deployment_type="serverless")
        results = []

        for i, case in enumerate(dataset):
            question = case["question"]
            reference = case["expected_answer"]

            for mode, answer in [("Without context", case["answer_no_context"]),
                                ("With context", case["answer_with_context"])]:
                prompt = f"""
                You are a strict and detailed evaluator for LLM answers.
                Evaluate the following answer according to the given dimensions.
                Give each score between 0 and 1 ({'0 = incorrect, 1 = perfect' if strict_mode else '0 = poor, 1 = excellent'}).

                [Question]
                {question}

                [Reference Answer]
                {reference}

                [Model Answer]
                {answer}

                Respond in JSON format as:
                {{
                "factuality": <float>,
                "completeness": <float>,
                "relevance": <float>,
                "faithfulness": <float>,
                }}
                """

                response = fw.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}]
                )

                raw_output = response.choices[0].message.content.strip()
                try:
                    start = raw_output.find("{")
                    end = raw_output.find("}", start)
                    if start != -1 and end != -1:
                        result = raw_output[start:end+1] 
                    parsed = json.loads(result)
                except Exception:
                    parsed = {"raw": raw_output}

                parsed.update({
                    "id": i + 1,
                    "mode": mode,
                    "question": question,
                    "expected_answer": reference,
                    "model_answer": answer
                })
                results.append(parsed)

        df = pd.DataFrame(results)
        return df