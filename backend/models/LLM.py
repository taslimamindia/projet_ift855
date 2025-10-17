from fireworks import LLM
from outils.dataset import Data


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

    def generate_QA(self, prompt) -> str:
        """Generate an answer using the LLM model.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: Generated response content from the LLM.
        """

        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat.completions.create(messages=messages)
        return response.choices[0].message.content