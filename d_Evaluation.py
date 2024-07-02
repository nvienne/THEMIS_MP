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
        "Chaque évaluation doit être accompagnée d'une justification détaillée, expliquant les raisons de l'attribution de la note, en mettant l'accent sur l'adéquation de la réponse aux critères d'évaluation. Votre jugement doit être fondé sur :\n"
        "- Le nom du critère d'évaluation.\n"
        "- Une description détaillée du critère.\n"
        "- Les éléments attendus pour répondre pleinement au critère.\n"
        "- L'analyse de la soumission reçue, en évaluant sa conformité avec les critères et les éléments attendus.\n\n"
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
            model="gpt-4-1106-preview", 
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

    tokens_used = response.usage.total_tokens
    usd_cost = (tokens_used / 1000000) * 10
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return evaluations, usd_cost


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