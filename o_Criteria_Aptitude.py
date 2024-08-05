from openai import OpenAI

def generate_criteria_aptitude(description_du_marché, model_name="gpt-4o-2024-05-13"):
    client = OpenAI(api_key="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")

    system_message = {
        "role": "system",
        "content": (
                """Vous êtes une IA spécialisée dans l'élaboration de critères d'aptitude pour les marchés publics, basés sur la description d'un marché spécifique. 
                Les critères d'aptitude sont les exigences minimales prouvant la capacité d'un soumissionnaire à exécuter un marché public. 
                Votre mission est de créer une liste de quatre critères respectant les principes fondamentaux suivants: non-discrimination et transparence, pertinence directe avec l'objet du marché, contribution au développement durable, et conformité avec les régulations légales. 
                Vous vous baserez sur les éléments les plus pertinents par rapport au marché spécifique.

                Pour chaque critère, incluez: son nom, une description, les critères d'acceptation ou de refus de l'offre, la logique, et le format de réponse attendu. 
                Veuillez utiliser une liste à puces pour présenter chaque critère et maintenir une mise en forme cohérente tout au long du texte.
                """
        )
    }

    user_message = {
        "role": "user",
        "content": f"Objet du marché : {description_du_marché}"
    }

    messages = [system_message, user_message]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.5,
        max_tokens=4096,
        frequency_penalty=0.5,
    )

    if response.choices and response.choices[0].message:
        criteria_content = response.choices[0].message.content
    else:
        criteria_content = "Response not available"

    tokens_used = response.usage.total_tokens
    usd_cost = (tokens_used / 1000) * 0.015

    return criteria_content, tokens_used, usd_cost

def generate_additional_aptitude(description_du_marché, previous_criteria, model_name):
    client = OpenAI(api_key="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")
    enriched_context = "\n".join(previous_criteria)

    system_message_content = (
        "Sur la base des critères précédemment générés :\n{}\n\n"
        "et en prenant en compte la description du marché '{}', "
        "veuillez générer quatre critères d'aptitude supplémentaires qui complètent les quatre critères générés. "
        "Chaque critère doit être détaillé avec : son nom, une description, les éléments d'appréciations, en respectant un format structuré."
    ).format(enriched_context, description_du_marché)

    system_message = {
        "role": "system",
        "content": system_message_content
    }

    user_message = {
        "role": "user",
        "content": "Générez des critères supplémentaires."
    }

    messages = [system_message, user_message]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.5,
        max_tokens=4000,
        frequency_penalty=0.5,
    )

    if response.choices and response.choices[0].message:
        additional_criteria_content = response.choices[0].message.content
    else:
        additional_criteria_content = "Response not available"

    tokens_used = response.usage.total_tokens
    usd_cost = (tokens_used / 1000) * 0.015

    return additional_criteria_content, tokens_used, usd_cost

def run_aptitude_generation(description_du_marché, model_name="gpt-4o-2024-05-13"):
    # Generate the initial set of criteria
    initial_criteria_content, initial_tokens_used, initial_usd_cost = generate_criteria_aptitude(description_du_marché, model_name)
    previous_criteria = initial_criteria_content.split('\n')

    # Generate additional criteria based on the initial set
    additional_criteria_content, additional_tokens_used, additional_usd_cost = generate_additional_aptitude(description_du_marché, previous_criteria, model_name)

    # Combine the initial and additional criteria contents
    combined_criteria_content = initial_criteria_content + '\n' + additional_criteria_content

    # Calculate the total tokens used and the total cost
    total_tokens_used = initial_tokens_used + additional_tokens_used
    total_usd_cost = initial_usd_cost + additional_usd_cost

    return combined_criteria_content, total_tokens_used, total_usd_cost
