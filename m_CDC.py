import chromadb
from openai import OpenAI

def initialize_collection(db_path, collection_name):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(collection_name)

    return collection, chroma_client

def cahier_des_charges(description, additional_info, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=12000):
    client = OpenAI(api_key="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")

    questions = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
        et des informations supplémentaires pertinentes : '{additional_info}', 
        vous devez exploiter votre propre raisonnement et savoir ainsi qu'une base de données exhaustive des lois, ordonnances, documentations officielles et décisions judiciaires relatives aux marchés publics en Suisse pour formuler des questions stratégiques. 
        Ces questions doivent aider l'utilisateur à définir son cahier des charges de manière exhaustive et pertinente. 
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
    cahier_des_charges = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
        et des informations supplémentaires pertinentes : '{additional_info}', 
        vous devez exploiter votre propre raisonnement et savoir pour  rédiger des paragraphes d'un cahier des charges en lien avec l'appel d'offres. 
        Les chapitres seront les suivants :
        1. Description détaillée du marché
        2. Objectifs du mandat
        3. Présentation des biens ou services achetés
        4. Eléments spécifiques du cahier des charges technique
        5. Organigramme, processus et responsabilités durant le mandat
        6. Propositions de système de suivi et KPI

        Assurez-vous que le ton corresponde à celui d'un document officiel et que les paragraphes soient exhaustifs."""

    cahier_des_charges_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": cahier_des_charges}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    cahier_des_charges_output = cahier_des_charges_completion.choices[0].message.content
    usage_cahier_des_charges = cahier_des_charges_completion.usage

    # Define the pricing
    price_per_million_input_tokens = 5.00  # in USD
    price_per_million_output_tokens = 15.00  # in USD

    input_tokens_phase1 = len(questions.split())
    output_tokens_phase1 = usage_questions.completion_tokens
    total_tokens_phase1 = input_tokens_phase1 + output_tokens_phase1

    input_tokens_phase2 = len(cahier_des_charges.split())
    output_tokens_phase2 = usage_cahier_des_charges.completion_tokens
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
        "Suggestions": cahier_des_charges_output,
        "Total_tokens_phase1": total_tokens_phase1,
        "Total_tokens_phase2": total_tokens_phase2,
        "Total_cost_phase1": total_cost_phase1,
        "Total_cost_phase2": total_cost_phase2
    }