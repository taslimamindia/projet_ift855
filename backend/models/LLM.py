from fireworks import LLM
from outils.dataset import Data
import langid
import pycountry


class Fireworks_LLM:
    def __init__(self, data:Data, model="llama4-maverick-instruct-basic", deployment_type="serverless"):
        """Connect to an LLM model via the Fireworks API.

        Args:
            data (Data): Data container providing API keys and other context.
            model (str, optional): Name of the LLM model. Defaults to "llama4-maverick-instruct-basic".
            deployment_type (str, optional): Deployment type. Defaults to "serverless".
        """

        self.data = data
        self.llm = LLM(model=model, deployment_type=deployment_type, api_key=self.data.fireworks_api_key)


    def generate_QA(self, prompt: str) -> str:
        """Generate an answer using the LLM model.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: Generated response content from the LLM.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat.completions.create(messages=messages)
        return response.choices[0].message.content

    
    def translate(self, prompt, target_language) -> str:
        """Translate text to a target language using the LLM model.

        Args:
            prompt (str): The input text to be translated.
            target_language (str): The target language for translation.

        Returns:
            str: Translated text from the LLM.
        """

        translation_prompt = f"Translate the following text to {target_language}:\n\n{prompt} respond only with the translated text."
        messages = [{"role": "user", "content": translation_prompt}]
        response = self.llm.chat.completions.create(messages=messages)
        return response.choices[0].message.content


    def detect_language(self, text: str) -> str:
        """ Detect language of a text using langid.
        
        Args:
            text (str): The input text whose language is to be detected.
        
        Returns:
            str: Detected language name (e.g., 'English', 'French').
        """

        try:
            # Try to get the language name from the 2-letter code
            if not text or not text.strip():
                return None

            if langid is None:
                raise RuntimeError(
                    "The 'langid' package is not installed. Install it with: pip install langid"
                )

            # langid.classify returns (iso_code, score). score is unbounded; convert to [0,1]
            code, _ = langid.classify(text)
            lang = pycountry.languages.get(alpha_2=code)
            if lang:
                return lang.name
            
        except Exception as e:
            raise RuntimeError(f"Unable to find language name for code: {code}") from e


    def detect_language_of_documents(self, documents: list[str]) -> str:
        """ Detect languages of a list of documents using langid.

        Args:
            documents (list of str): The input texts whose languages are to be detected.

        Returns:
            str: Detected dominant language name (e.g., 'English', 'French').
        """

        results = {}
        
        for text in documents:        
            lang = self.detect_language(text)
            if results.get(lang, False):
                results[lang] += 1
            else:
                results[lang] = 1

        return max(results.items(), key=lambda x: x[1])[0]
