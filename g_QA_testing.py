import chromadb
from openai import OpenAI
import pandas as pd


def initialize_collection(db_path, collection_name):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(collection_name)

    return collection, chroma_client

def embed_text_with_ada(text):
    openai_client = OpenAI(api_key="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")
    response = openai_client.embeddings.create(input=text, model="text-embedding-ada-002")
    embeddings = [item.embedding for item in response.data]

    return embeddings

def extract_information(response):
    if not response or 'metadatas' not in response or 'distances' not in response:
        print("Invalid response format.")
        return {}

    results = response['metadatas'][0]
    distances = response['distances']

    # Initialize a dictionary to hold the grouped documents
    grouped_documents = {'LEX': [], 'ATF': [], 'ATC': [], 'DOC': []}

    # Group documents by their type
    for i, doc in enumerate(results):
        doc_type = doc.get('type', 'N/A')
        if doc_type in grouped_documents:
            grouped_documents[doc_type].append({
                "Document": doc.get('filename', 'N/A'),
                "Extrait": ' '.join(doc.get('chunk', '').split()[:50]) + '...',
                "Juridiction": doc.get('juridiction', 'N/A'),
                "Pertinence": f"{round(distances[i], 3):.3f}"
            })

    # Create a dataframe for each group and maintain the order of importance
    dataframes = {doc_type: pd.DataFrame(documents) for doc_type, documents in grouped_documents.items() if documents}

    return dataframes

    # if not response or 'metadatas' not in response or 'distances' not in response:
    #     print("Invalid response format.")
    #     return
    
    # results = response['metadatas'][0]  
    # distances = response['distances']   

    # table = PrettyTable()
    # table.field_names = ["Filename", "Chunk Start", "Jurisdiction", "Distance"]
    
    # for i, doc in enumerate(results):
    #     filename = doc.get('filename', 'N/A')
    #     chunk_start = ' '.join(doc.get('chunk', '').split()[:17]) + '...'
    #     jurisdiction = doc.get('juridiction', 'N/A')  
    #     distance = f"{round(distances[i], 3):.3f}" if i < len(distances) else 'N/A'
        
    #     # Add row to the table
    #     table.add_row([filename, chunk_start, jurisdiction, distance])

    # print(table)

def query_chroma_db(collection, question, n_results, type=None, juridiction=None, include_data=["documents", "metadatas", "distances"]):
    try:
        query_embeddings = embed_text_with_ada(question)
        
        # Initially, apply only the type filter if specified, ignore juridiction filter
        metadata_filter = {}
        if type:
            metadata_filter["type"] = {"$eq": type}

        # Fetch more results than needed to manually filter later; adjust n_results as feasible
        initial_n_results = n_results * 2 

        response = collection.query(
            query_embeddings=query_embeddings,
            n_results=initial_n_results,
            where=metadata_filter,
            include=include_data
        )

        # Extract metadatas and distances
        metadatas = response['metadatas'][0]
        distances = response['distances'][0]

        # Apply juridiction filter for "LEX" type and distance filter
        filtered_metadatas = []
        filtered_distances = []

        for i, doc in enumerate(metadatas):
            # Skip documents that do not meet the juridiction criteria for LEX types or if distance is higher than 0.25
            if distances[i] <= 0.25 and ((doc.get('type') == 'LEX' and juridiction and doc.get('juridiction') == juridiction) or doc.get('type') != 'LEX'):
                filtered_metadatas.append(doc)
                filtered_distances.append(distances[i])

        # Limit the results to the originally requested number after filtering
        final_metadatas = filtered_metadatas[:n_results]
        final_distances = filtered_distances[:n_results]

        # Construct the final response
        final_response = {'metadatas': [final_metadatas], 'distances': final_distances}
        return final_response

    except Exception as e:
        print(f"Error querying Chroma DB with ada embeddings: {e}")
        return None
    
def QA(question, top_chunks, model_name, completion_tokens, max_question_tokens):
    client = OpenAI(api_key="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")

    # Extract the context from top_results
    context = ""
    context_tokens = 0
    for metadata_list in top_chunks['metadatas']:
        for result in metadata_list:
            document_text = result['chunk']  
            chunk_tokens = len(document_text.split())
            if context_tokens + chunk_tokens <= max_question_tokens:
                context += f"Document ID: {result.get('filename', 'Unknown')}\n{document_text}\n\n"  
                context_tokens += chunk_tokens
            else:
                print("Token limit reached, additional documents are not added.")
                break
        else:
            print("Token limit reached, additional documents are not added.")
            break

    if not context:
        print("No valid results received from Chroma DB.")
        return None, None

    messages = [
        {
            "role": "system",
            "content": (
                "En tant qu'assistant virtuel spécialisé dans les marchés publics suisses, votre mission est de fournir des réponses claires et exhaustives aux questions des utilisateurs. "
                "Vos réponses doivent être fondées sur les normes et réglementations légales les plus actuelles et pertinentes en matière de marchés publics. "
                "Dans vos réponses, accordez la priorité aux éléments suivants :\n"
                "- L'application des lois fédérales, des réglementations cantonales et des décisions judiciaires pertinentes.\n"
                "- La clarté et l'accessibilité de l'information, garantissant que les utilisateurs de divers horizons puissent comprendre le processus de marché public.\n"
                "- L'identification des ambiguïtés dans les questions des utilisateurs et la fourniture de clarifications lorsque cela est nécessaire. Si une question ne peut être directement répondue en raison d'informations insuffisantes, guidez l'utilisateur sur la façon de raffiner leur demande pour une assistance plus précise.\n"
                "Votre rôle est de démystifier le processus de marché public, le rendant plus accessible et compréhensible pour tous les acteurs, tout en adhérant strictement aux principes de non-discrimination, de transparence et de conformité légale."
                "\n\nSections de contexte :\n{context}\n\nQuestion :\n{users_question}\n\nRéponse :"
            )
        },
        {"role": "user", "content": question}
    ]
    
    messages[0]['content'] = messages[0]['content'].format(context=context, users_question=question)

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1,
        max_tokens=completion_tokens
    )

    answer = completion.choices[0].message.content  
    tokens_used = completion.usage.total_tokens 
    # print(answer)

    usd_cost = (tokens_used / 1000000) * 10
    # print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost


# Original question 1 expanded
question_1a = "Quels critères d'aptitude techniques sont requis pour une entreprise IT souhaitant soumettre une offre pour le développement d'une application mobile dans un marché public ?"
question_1b = "Dans le cadre d'un marché public visant le développement et la maintenance sur cinq ans d'un système de gestion des ressources pour une municipalité, quels critères d'aptitude spécifiques à l'expertise en bases de données et en cybersécurité sont attendus pour une entreprise IT ?"

# Original question 2 expanded
question_2a = "Quel type de preuve financière peut être fourni par une start-up en restauration pour un marché public de services de cantine ?"
question_2b = "Lors de la candidature à un contrat pluriannuel pour la gestion des services de restauration d'une institution gouvernementale, comment une petite entreprise culinaire sans historique financier long peut-elle efficacement prouver sa stabilité financière et sa capacité à gérer les fluctuations saisonnières de la demande ?"

# Original question 3 expanded
question_3a = "Quels sont les processus de suivi que doit implémenter une municipalité pour garantir la transparence dans l'attribution des marchés publics de rénovation urbaine ?"
question_3b = "Face à des projets d'infrastructure d'envergure tels que la construction d'une nouvelle ligne de tramway, quelles procédures détaillées de surveillance et d'audit une ville doit-elle mettre en place pour assurer une transparence optimale et prévenir les risques de corruption tout au long du cycle du marché public ?"

# Original question 4 expanded
question_4a = "Quels types de rapports environnementaux sont généralement requis pour une entreprise de BTP dans le cadre d'un marché public portant sur la rénovation de bâtiments scolaires ?"
question_4b = "Pour un projet de grande envergure comme la construction d'un nouveau complexe hospitalier, pouvez-vous décrire le plan d'action et les rapports périodiques sur l'impact environnemental que doit fournir le prestataire en termes d'émissions, de gestion des déchets et de consommation d'énergie, selon les obligations légales de reporting environnemental ?"

# Original question 5 expanded
question_5a = "En quoi la procédure ouverte pour les marchés de fournitures médicales se différencie-t-elle de la procédure avec négociation en termes d'accès aux documents d'appel d'offres ?"
question_5b = "Dans un contexte de pandémie où l'achat de matériel médical devient critique, quelles sont les implications pratiques de choisir une procédure ouverte plutôt qu'une procédure sur invitation concernant la rapidité de mise en œuvre, la concurrence et la transparence des processus pour l'acquisition de respirateurs et de matériel de protection individuelle ?"

# Original question 6 expanded
question_6a = "Quel est le processus d'évaluation pour déterminer l'offre économiquement la plus avantageuse dans un appel d'offres pour des services d'audit légal ?"
question_6b = "Lors de la sélection d'un cabinet d'avocats pour représenter une agence gouvernementale dans des litiges internationaux, comment les critères d'évaluation financière, d'expertise spécifique en droit international et de performance passée sont-ils pondérés pour déterminer l'offre économiquement la plus avantageuse ?"

questions = [question_1a, question_1b, question_2a, question_2b, question_3a, question_3b, question_4a, question_4b, question_5a, question_5b, question_6a, question_6b]

db_path = r"E:\MP\3. Data base"
collection = "THEMIS_test"


collection, client = initialize_collection(db_path, collection)

for question in questions:
    print(f"Question: {question}")
    top_chunks = query_chroma_db(collection, question, n_results=15, type=None, juridiction=None, include_data=["documents", "metadatas", "distances"])
    answer, cost = QA(question, top_chunks, model_name="gpt-4-1106-preview", completion_tokens=4000, max_question_tokens=8000)
    print(f"Answer: {answer}\nCost: ${cost:.4f}\n")

