from openai import OpenAI
import pandas as pd
from prettytable import PrettyTable



def evaluate_submissions(criteria_name, criteria_description, expected_elements, submissions):
    client = OpenAI(api_key="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")

    evaluations = []

    # Prepare the system message
    system_message = {
        "role": "system",
        "content": (
       "En tant qu'évaluateur pour les marchés publics, votre rôle est crucial pour assurer un processus d'adjudication juste, transparent et équitable." 
       "Vous évaluerez les réponses des entreprises avec rigueur, en suivant une échelle de notation de 0 à 5, où chaque note reflète une évaluation précise :\n"
            "- 0 : Vide - la réponse est vide.\n"
            "- 1 : Insuffisant -  le réponse ne correspond pas aux attentes. \n"
            "- 2 : Partiellement suffisant - la réponse partielle aux attentes.\n"
            "- 3 : Satisfaisant - la réponse répond aux attentes minimales, mais ne présente aucun avantage particulier par rapport aux autres candidats ou soumissionnaires .\n"
            "- 4 : Bon et avantageux - la réponse présente un minimum d'avantages, ceci sans tomber dans la surqualité ou la surqualification.\n"
            "- 5 : Très intéressant - la réponse présente beaucoup d'avantages particuliers par raport aux autres réponse.\n\n"
        "Chaque évaluation doit respecter le format suivant "
        "- Le nom du soumissionnaire.\n"
        "- La note donnée.\n"
        "- Les points positifs et négatifs.\n"
        "- Le raisonnement pour arriver à la note donnée.\n"
        "- Les éléments attendus pour avoir une meilleure notes.\n\n"
        )
    }

    for submission in submissions:
        # Prepare the user message with the specific submission details
        user_message = {
            "role": "user",
            "content": f"Nom du critère: {criteria_name}\nDescription du critère: {criteria_description}\nÉléments attendus: {expected_elements}\nSoumission: {submission}"
        }

        # Construct the messages list for the API call
        messages = [system_message, user_message]

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o-2024-05-13", 
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            frequency_penalty=0.0,
            presence_penalty=0.1
        )

        # Correct way to access the response content
        if response.choices and response.choices[0].message:
            evaluation_content = response.choices[0].message.content
        else:
            evaluation_content = "Response not available"

        evaluations.append(evaluation_content)

    # Prepare the second system message
    system_message_2 = {
        "role": "system",
        "content": (
            "Prenez les évaluations des soumissions précédentes et formatez-les sous forme de tableau avec les colonnes suivantes :"
            " Soumissionnaire, Note, Raisonnement. "
        )
    }

    # Prepare the user message for the second API call
    user_message_2 = {
        "role": "user",
        "content": "\n\n".join(evaluations)
    }

    # Construct the messages list for the second API call
    messages_2 = [system_message_2, user_message_2]

    # Make the second API call
    response_2 = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=messages_2,
        temperature=0.3,
        max_tokens=2048,
        frequency_penalty=0.0,
        presence_penalty=0.1
    )

    # Correct way to access the response content
    if response_2.choices and response_2.choices[0].message:
        formatted_table = response_2.choices[0].message.content
    else:
        formatted_table = "Response not available"

    tokens_used = response_2.usage.total_tokens
    usd_cost = (tokens_used / 1000000) * 10
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    cleaned_formatted_table = formatted_table.replace("<br>", "\n")

    return evaluations, cleaned_formatted_table, usd_cost


    # tokens_used = response.usage.total_tokens
    # usd_cost = (tokens_used / 1000000) * 10
    # print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    # return evaluations, usd_cost


# # Example usage
# submissions = [
#     "Our proposal includes the use of recycled materials, solar panels for energy, and a detailed environmental impact report.",
#     "We plan to implement a comprehensive energy-saving system, but without specifics on materials used.",
#     "Our project does not specifically address sustainability but focuses on cost-efficiency.",
#     "We use cutting-edge technology to ensure minimal environmental impact and include an extensive environmental impact assessment.",
#     "Our submission includes detailed plans for material reuse and energy conservation, surpassing standard requirements."
# ]

# criteria_name = "Sustainability"
# criteria_description = "The project should minimize environmental impact and promote energy efficiency."
# expected_elements = "Details on materials used, energy saving measures, and environmental impact assessments."

# evaluations, usd_cost = evaluate_submissions(criteria_name, criteria_description, expected_elements, submissions)
# for idx, evaluation in enumerate(evaluations, start=1):
#     print(f"Evaluation for submission {idx}:\n{evaluation}\n")