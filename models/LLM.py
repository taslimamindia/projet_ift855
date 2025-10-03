from fireworks import LLM


def connexion_to_llm(model="llama4-maverick-instruct-basic", deployment_type="serverless", fireworks_api_key="fw_3Zg5B7CUKag67HsSZjCwwbwx"):
    """
        Connexion au modèle LLM via l'API Fireworks.
    
    Args:
        model (str, optional): Nom du modèle LLM. Defaults to "llama4-maverick-instruct-basic".
        deployment_type (str, optional): Type de déploiement. Defaults to "serverless".
        api_key (str, optional): Clé API pour Fireworks. Defaults to FIREWORKS_API_KEY.
    """

    llm = LLM(model=model, deployment_type=deployment_type, api_key=fireworks_api_key)
    
    return llm

def generate_answer(llm, query=None, context=None, last_response=None):
    """
        Génère une réponse en utilisant le modèle LLM.

    Args:
        llm: Instance du modèle LLM.
        query (str, optional): La requête de l'utilisateur. Defaults to None.
        context (str, optional): Le contexte pertinent pour la requête. Defaults to None.
        last_response (str, optional): La dernière réponse générée par le modèle. Defaults to None.
    """
 
    prompt = []

    if context:
        prompt.append({"role": "system", "content": context})

    if last_response:
        prompt.append({"role": "assistant", "content": last_response})

    if query:
        prompt.append({"role": "user", "content": query})


    response = llm.chat.completions.create(messages=prompt)
    return response.choices[0].message.content