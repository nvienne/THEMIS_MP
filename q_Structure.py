from openai import OpenAI

def structure_dossier_part1(conditions_de_participation, model_name="gpt-4o-2024-05-13", completion_tokens=1333):
    client = OpenAI(api_key="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")

    checklist_prompt_part1 = f"""Vous êtes une IA spécialisée en génération de checklist d'attestations et de documents à fournir par le soumissionaire d'un marché public. 

    veuillez produire une checklist comprenant les documents requis et la méthode d'évaluation pour les éléments suivants:
    1. Conditions de participation:
    {conditions_de_participation}

    Pour chaque élément, incluez: le nom de l'élément, le nom du document requis et les critères d'évaluation pour accepter ou éliminer une offre. 
    Assurez-vous que les informations soient précises, concises et présentées sous forme de tableau avec les colonnes "Elément", "Document requis", "Accepté" et "Eliminé". Ce tableau sera utilisé comme feuille de contrôle lors de l'ouverture des offres.
    """

    checklist_completion_part1 = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": checklist_prompt_part1}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    checklist_output_part1 = checklist_completion_part1.choices[0].message.content
    usage_checklist_part1 = checklist_completion_part1.usage

    return checklist_output_part1, usage_checklist_part1


def structure_dossier_part2(criteres_aptitude, model_name="gpt-4o-2024-05-13", completion_tokens=1333):
    client = OpenAI(api_key="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")

    checklist_prompt_part2 = f"""Vous êtes une IA spécialisée en génération de checklist d'attestations et de documents à fournir par le soumissionaire d'un marché public. 

    veuillez produire une checklist comprenant les documents requis et la méthode d'évaluation pour les éléments suivants:
    2. Critères d'aptitude:
    {criteres_aptitude}

    Pour chaque élément, incluez: le nom de l'élément, le nom du document requis et les critères d'évaluation pour accepter ou éliminer une offre. 
    Assurez-vous que les informations soient précises, concises et présentées sous forme de tableau avec les colonnes "Elément", "Document requis", "Accepté" et "Eliminé". Ce tableau sera utilisé comme feuille de contrôle lors de l'ouverture des offres.
    """

    checklist_completion_part2 = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": checklist_prompt_part2}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    checklist_output_part2 = checklist_completion_part2.choices[0].message.content
    usage_checklist_part2 = checklist_completion_part2.usage

    return checklist_output_part2, usage_checklist_part2


def structure_dossier_part3(criteres_adjudication, model_name="gpt-4o-2024-05-13", completion_tokens=1333):
    client = OpenAI(api_key="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")

    checklist_prompt_part3 = f"""Vous êtes une IA spécialisée en génération de checklist d'attestations et de documents à fournir par le soumissionaire d'un marché public. 

    veuillez produire une checklist comprenant les documents requis et la méthode d'évaluation pour les éléments suivants:
    3. Critères d'adjudication:
    {criteres_adjudication}

    Pour chaque élément, incluez: le nom de l'élément, le nom du document requis et les critères d'évaluation pour accepter ou éliminer une offre. 
    Assurez-vous que les informations soient précises, concises et présentées sous forme de tableau avec les colonnes "Elément", "Document requis", "Eléments d'appréciation". Ce tableau sera utilisé comme feuille de contrôle lors de l'ouverture des offres.
    """

    checklist_completion_part3 = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": checklist_prompt_part3}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    checklist_output_part3 = checklist_completion_part3.choices[0].message.content
    usage_checklist_part3 = checklist_completion_part3.usage

    return checklist_output_part3, usage_checklist_part3


def structure_dossier(conditions_de_participation, criteres_aptitude, criteres_adjudication, model_name="gpt-4o-2024-05-13", completion_tokens=4000):
    output_part1, usage_part1 = structure_dossier_part1(conditions_de_participation, model_name, completion_tokens // 3)
    output_part2, usage_part2 = structure_dossier_part2(criteres_aptitude, model_name, completion_tokens // 3)
    output_part3, usage_part3 = structure_dossier_part3(criteres_adjudication, model_name, completion_tokens // 3)

    checklist_output = output_part1 + "\n\n" + output_part2 + "\n\n" + output_part3

    # Define the pricing
    price_per_million_input_tokens = 5.00  # in USD
    price_per_million_output_tokens = 15.00  # in USD

    input_tokens_part1 = len(output_part1.split())
    input_tokens_part2 = len(output_part2.split())
    input_tokens_part3 = len(output_part3.split())
    input_tokens = input_tokens_part1 + input_tokens_part2 + input_tokens_part3

    output_tokens_part1 = usage_part1.completion_tokens
    output_tokens_part2 = usage_part2.completion_tokens
    output_tokens_part3 = usage_part3.completion_tokens

    output_tokens = output_tokens_part1 + output_tokens_part2 + output_tokens_part3
    total_tokens = input_tokens + output_tokens

    # Calculate the cost
    cost_input = (input_tokens / 1_000_000) * price_per_million_input_tokens
    cost_output = (output_tokens / 1_000_000) * price_per_million_output_tokens
    total_cost = cost_input + cost_output

    cleaned_checklist_output = checklist_output.replace("<br>", "\n")

    # Update the return dictionary to include costs
    return {
        "Checklist": cleaned_checklist_output,
        "Total_tokens": total_tokens,
        "Total_cost": total_cost
    }