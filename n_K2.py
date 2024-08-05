import chromadb
from openai import OpenAI

def initialize_collection(db_path, collection_name):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(collection_name)

    return collection, chroma_client

def K2(description, additional_info, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=12000):
    client = OpenAI(api_key="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")

    questions = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
        et des informations supplémentaires pertinentes : '{additional_info}', 
        vous devez exploiter votre propre raisonnement et savoir ainsi qu'une base de données exhaustive des lois, ordonnances, documentations officielles et décisions judiciaires relatives aux marchés publics en Suisse pour formuler des questions stratégiques. 
        Ces questions doivent aider l'utilisateur à définir 
        1. Les conditions de participation : délai de remise des offres, forme de l'offre, motifs d'exclusion, consortium autorisé ou non, sous-traitance autorisée ou non, variantes d'offres possibles, allotissement.  
        2: Les critères d'aptitude : le soumissionnaire doit posséder au minimum les compétences, aptitudes et formations mentionnées pour l’exécution du marché, sous peine d’exclusion de la procédure.
        3. Si des visites ont du sens et sous quelle forme
        Assurez-vous que les questions sont précises, axées sur l'action et pertinentes par rapport à l'objet du marché"""

    questions_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": questions}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    strategy_questions_guidelines = questions_completion.choices[0].message.content
    usage_questions = questions_completion.usage

    # Phase 2: Generate proposals for cahier des charges
    k2 = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
        et des informations supplémentaires pertinentes : '{additional_info}', 
        vous devez exploiter votre propre raisonnement et savoir ainsi qu'une base de données exhaustive des lois, ordonnances, documentations officielles et décisions judiciaires relatives aux marchés publics en Suisse pour formuler des propositions claires et détaillées. 
        Ces propositions doivent porter sur les éléments suivants :
        1. Les conditions de participation : délai de remise des offres, forme de l'offre, motifs d'exclusion, consortium autorisé ou non, sous-traitance autorisée ou non, variantes d'offres possibles, allotissement.  
        2: Les critères d'aptitude : le soumissionnaire doit posséder au minimum les compétences, aptitudes et formations mentionnées pour l’exécution du marché, sous peine d’exclusion de la procédure.
        3. Si des visites ont du sens et sous quelle forme

        Assurez-vous que les propositions sont précises, axées sur l'action et pertinentes par rapport à l'objet du marché"""

    k2_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": k2}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    k2_output = k2_completion.choices[0].message.content
    usage_k2 = k2_completion.usage

    # Define the pricing
    price_per_million_input_tokens = 5.00  # in USD
    price_per_million_output_tokens = 15.00  # in USD

    input_tokens_phase1 = len(questions.split())
    output_tokens_phase1 = usage_questions.completion_tokens
    total_tokens_phase1 = input_tokens_phase1 + output_tokens_phase1

    input_tokens_phase2 = len(k2.split())
    output_tokens_phase2 = usage_k2.completion_tokens
    total_tokens_phase2 = input_tokens_phase2 + output_tokens_phase2

    # Calculate the cost for phase 1
    cost_input_phase1 = (input_tokens_phase1 / 1_000_000) * price_per_million_input_tokens
    cost_output_phase1 = (output_tokens_phase1 / 1_000_000) * price_per_million_output_tokens
    total_cost_phase1 = cost_input_phase1 + cost_output_phase1

    # Calculate the cost for phase 2
    cost_input_phase2 = (input_tokens_phase2 / 1_000_000) * price_per_million_input_tokens
    cost_output_phase2 = (output_tokens_phase2 / 1_000_000) * price_per_million_output_tokens
    total_cost_phase2 = cost_input_phase2 + cost_output_phase2

    # Update the return dictionary to include costs
    return {
        "Questions": strategy_questions_guidelines,
        "Suggestions": k2_output,
        "Total_tokens_phase1": total_tokens_phase1,
        "Total_tokens_phase2": total_tokens_phase2,
        "Total_cost_phase1": total_cost_phase1,
        "Total_cost_phase2": total_cost_phase2
    }