from openai import OpenAI

def generate_recevabilite(description_du_marché, model_name="gpt-4o-2024-05-13"):
    client = OpenAI(api_key="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")

    system_message = {
        "role": "system",
        "content": (
                """Vous êtes une IA spécialisée dans l'élaboration de conditions de recevabilité des offres reçues dans le cadre d'un marché public. 
                En vous basant sur la description d'un marché spécifique, vous produirez des propositions sur l'acceptabilité ou non des éléments suivants :
                -  des consortiums d’entreprises, et si oui à quelles conditions ; 
                -  la sous-traitance des prestations, et si oui à quelles conditions ; 
                -  des variantes d'offres, et si oui à quelles conditions ; 
                -  des offres partielles, et si oui à quelles conditions ; 
                -  des entreprises pré-impliquées, et si oui à quelles conditions ; 

                Pour chaque proposition, incluez: une description, la raison pour laquelle le critère devrait être utilisé, les éléments d'appréciation et le format de réponse attendu. 
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

def participation_CROMP(description_du_marché, model_name):
    client = OpenAI(api_key="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")

    liste_annexes = f"""Vous êtes une IA spécialisée en contrôle des conditions de participations d'un marché public.
    Compte tenu de la description de l'objet de l'appel d'offres : '{description_du_marché}', 
    veuillez produire une checklist comprenant les documents requis et la méthode d'évaluation pour les annexes P1, P2a, P2b, P2c, R15, P6, et P7, en vous basant sur les critères et documents requis suivants:

    - P1: Engagement sur l'honneur
        - Document requis : Engagement spécifiant que le soumissionnaire et ses sous-traitants éventuels respectent les conditions de participation mentionnées et qu'ils les respecteront pendant la procédure et l'exécution ultérieure du marché.
        - Accepté : Attestation fournie, datée et signée
        - Eliminé : Attestation pas fournie ou non signée

    - P2a: Profil du soumissionnaire correspondant à la nature du marché mis en concurrence
        - Document requis : Copie de l'extrait du registre du commerce, preuve de l'inscription sur un registre professionnel reconnu officiellement ou copie du diplôme professionnel, ceci y compris pour les sous-traitants.
        - Accepté : Attestation fournie par un organisme officiel ou par une association professionnelle reconnue
        - Eliminé : Attestation pas fournie ou preuve jugée comme inofficielle

    - P2b: Intégrité sociale et fiscale du soumissionnaire
        - Documents requis :  Attestations du paiement des cotisations sociales (AVS, AI, APG, AC, AF, LPP ou leur équivalent), preuves cotisations assurance RC + assurance-accident, attestations fiscales d'entreprise, et fiscales à la source pour le personnel étranger, preuve assujettissement TVA, ceci y compris pour les sous-traitants. 
        - Accepté : Attestations fournies, complètes et signées par un organisme officiel ou par une association professionnelle reconnue officiellement
        - Attestations pas fournies, incomplètes, pas en ordre, pas signées par un organisme officiel ou dont la date de validité est dépassée

    - P2c: Respect des usages professionnels et des conditions de base relatives à la protection des travailleurs
        - Document requis : Preuve de la signature d'une Convention collective de travail (CCT) ou d'un contrat type de travail (CTT) applicable au lieu d'exécution, ceci en rapport avec le marché mis en concurrence ou engagement à en respecter les conditions auprès de l'organisme compétent du lieu d'exécution, ceci y compris pour les sous-traitants.
        - Accepté : Attestation fournie, complète et signée par un organisme officiel ou par une association professionnelle reconnue officiellement
        - Eliminé : Attestation pas fournie, pas en ordre, pas signée par un organisme officiel ou dont la date de validité est dépassée

    - R15: Annonce des sous-traitants prévus pour l'exécution du marché
        - Document requis : Fiche d'annonce des sous-traitants nécessaires pour l'exécution du marché.
        - Accepté : Le soumissionnaire a annoncé ses sous-traitants ou il confirme ne faire appel à aucun sous-traitant pour l'exécution du marché
        - Eliminé : Le soumissionnaire n'a pas fourni d'indication et ou il n'a pas confirmé qu'il ne fera pas appel à des sous-traitants pour l'exécution du marché

    - P6: Engagement à respecter l'égalité entre femmes et hommes
        - Document requis : Engagement à respecter les dispositions légales concernant l'égalité entre femmes et hommes et plus particulièrement l'égalité salariale.
        - Accepté : Engagement sur l'honneur daté et signé
        - Eliminé : Engagement non fourni ou non signé

    - P7: Engagement à respecter les conditions de travail internationales
        - Document requis : Engagement à respecter les conventions fondamentales de l’Organisation Internationale du Travail.
        - Accepté : Engagement sur l'honneur daté et signé
        - Eliminé : Engagement non fourni ou non signé
    """

    system_message = {
        "role": "system",
        "content": liste_annexes
    }

    user_message = {
        "role": "user",
        "content": "Générez la Checklist."
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

def run_conditions_generation(description_du_marché, model_name="gpt-4o-2024-05-13"):
    # Generate the initial set of criteria
    conditions_recevabilite, initial_tokens_used, initial_usd_cost = generate_recevabilite(description_du_marché, model_name)

    # Generate additional criteria based on the initial set
    list_annexes, additional_tokens_used, additional_usd_cost = participation_CROMP(description_du_marché, model_name)

    # Calculate the total tokens used and the total cost
    total_tokens_used = initial_tokens_used + additional_tokens_used
    total_usd_cost = initial_usd_cost + additional_usd_cost

    return conditions_recevabilite, list_annexes, total_tokens_used, total_usd_cost
