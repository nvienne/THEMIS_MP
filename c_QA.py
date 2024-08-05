import chromadb
from openai import OpenAI
import pandas as pd



######### BASE

def initialize_collection(db_path, collection_name):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(collection_name)

    return collection, chroma_client

def embed_text_with_ada(text):
    openai_client = OpenAI(api_key="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")
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
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

def query_chroma_db_qa(collection, question, n_results, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"]):
    try:
        # Generate embeddings for the question
        query_embeddings = embed_text_with_ada(question)

        # Prepare metadata filters
        metadata_filter = {}
        if type_filter and juridiction_filter:
            metadata_filter = {
                "$and": [
                    {"type": {"$eq": type_filter}},
                    {"juridiction": {"$eq": juridiction_filter}}
                ]
            }
        elif type_filter:
            metadata_filter = {"type": {"$eq": type_filter}}
        elif juridiction_filter:
            metadata_filter = {"juridiction": {"$eq": juridiction_filter}}

        # Print metadata filters for debugging
        print(f"Metadata filter: {metadata_filter}")

        # Query the collection
        response = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=metadata_filter,
            include=include_data
        )

        # Check and log the response
        if 'ids' in response and len(response['ids']) > 0:
            # Log each document's ID and metadata
            # for doc_id, metadata, distance in zip(response['ids'][0], response['metadatas'][0], response['distances'][0]):
            #     print(f"Document ID: {doc_id}, Metadata: {metadata}, Distance: {distance:.2f}")
            return response
        else:
            print("No results found with the given filters.")
            return None
    
    except Exception as e:
        print(f"Error querying Chroma DB with ada embeddings: {e}")
        return None
    
def QA_initial(question, top_chunks, model_name, completion_tokens, max_question_tokens):
    client = OpenAI(api_key="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")

    # Check if top_chunks is None
    if top_chunks is None or 'metadatas' not in top_chunks or not top_chunks['metadatas']:
        print("No valid results received from Chroma DB.")
        return None, None

    # Extract the context from top_results
    context = ""
    context_tokens = 0
    for metadata_list in top_chunks['metadatas']:
        for result in metadata_list:
            document_text = result.get('chunk', '')
            chunk_tokens = len(document_text.split())
            if context_tokens + chunk_tokens <= max_question_tokens:
                context += f"Document ID: {result.get('filename', 'Unknown')}\n{document_text}\n\n"
                context_tokens += chunk_tokens
            else:
                print("Token limit reached, additional documents are not added.")
                break
        else:
            print("No tokens")
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
    print(answer[:100])

    usd_cost = (tokens_used / 1000000) * 5
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost


######### TESTING

def QA_OLLAMA(question, top_chunks, max_question_tokens, completion_tokens = 4000, model_name="llama3:latest"):
    # Verify the model is available
    models = [model['name'] for model in ollama.list()['models']]
    print(models)
    
    if model_name not in models:
        print(f"{model_name} model is not available. Pulling the model now.")
        ollama.pull(model_name)
    
    # Extract the context from top_chunks
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

    # Create a chat completion using Ollama
    response = ollama.chat(model=model_name, messages=messages)
    
    answer = response['message']['content']
    print(answer[:100])

    return answer, None

def count_keyword_matches(chunk, keywords):
    # Count the number of keywords that appear in the chunk
    return sum(chunk.lower().count(keyword.lower()) for keyword in keywords)

def query_chroma_db_qa_keywords(collection, question, n_results, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"], keywords=None):
    try:
        # Generate embeddings for the question
        query_embeddings = embed_text_with_ada(question)

        # Prepare metadata filters
        metadata_filter = {}
        if type_filter:
            metadata_filter["Type"] = {"$eq": type_filter}
        if juridiction_filter:
            metadata_filter["Juridiction"] = {"$eq": juridiction_filter}

        # Query the collection
        response = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=metadata_filter,
            include=include_data
        )

        # Rank chunks based on keyword matches
        chunks = response['metadatas'][0]
        keyword_stats = {keyword: {"count": 0, "documents": []} for keyword in keywords}
        no_match_chunks = 0

        scored_chunks = []
        for chunk in chunks:
            match_count = 0
            for keyword in keywords:
                if keyword.lower() in chunk['chunk'].lower():
                    keyword_stats[keyword]["count"] += chunk['chunk'].lower().count(keyword.lower())
                    keyword_stats[keyword]["documents"].append(chunk.get('filename', 'Unknown'))
                    match_count += chunk['chunk'].lower().count(keyword.lower())
            if match_count > 0:
                scored_chunks.append((chunk, match_count))
            else:
                no_match_chunks += 1

        # Sort chunks by the number of keyword matches in descending order
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Select the top n_results chunks
        top_chunks = [chunk for chunk, score in scored_chunks[:n_results]]

        # Print statistics
        print("List of keywords found in the chunks:")
        for keyword, stats in keyword_stats.items():
            if stats["count"] > 0:
                print(f"Keyword: {keyword}, Count: {stats['count']}, Documents: {set(stats['documents'])}")
        print(f"Number of chunks without any match: {no_match_chunks}")

        return top_chunks

    except Exception as e:
        print(f"Error querying Chroma DB with ada embeddings: {e}")
        return None

def reformulate_query(query, model_name, reformulation_tokens=100):
    client = OpenAI(api_key="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")

    reformulation_prompt = (
        "Please reformulate and expand the following query to make it more comprehensive and detailed: \n\n"
        f"Query: {query}\n\nReformulated and Expanded Query:"
    )

    reformulation_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": reformulation_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.3,
        max_tokens=reformulation_tokens
    )

    reformulated_query = reformulation_completion.choices[0].message.content
    return reformulated_query

def QA_reformulated(question, top_chunks, model_name, completion_tokens, max_question_tokens):
    # Step 1: Reformulate and expand the query
    reformulated_question = reformulate_query(question, model_name)

    client = OpenAI(api_key="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")

    # Extract the context from top_chunks
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
            print("No tokens")
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
        {"role": "user", "content": reformulated_question}
    ]
    
    messages[0]['content'] = messages[0]['content'].format(context=context, users_question=reformulated_question)

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1,
        max_tokens=completion_tokens
    )

    answer = completion.choices[0].message.content  
    tokens_used = completion.usage.total_tokens 
    print(answer[:100])

    usd_cost = (tokens_used / 1000000) * 5
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost

def QA_OG_modified(question, top_chunks, model_name, completion_tokens, max_question_tokens):
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
            print("No tokens")
            break

    if not context:
        print("No valid results received from Chroma DB.")
        return None, None

    messages = [
        {
            "role": "system",
            "content": (
                "Vous êtes un assistant virtuel expert en marchés publics suisses. Votre objectif est de fournir des réponses précises, complètes et fondées sur les dernières normes et réglementations légales en matière de marchés publics en Suisse. "
                "Suivez ces directives pour formuler vos réponses :\n\n"
                "1. **Application des Lois et Réglementations**:\n"
                "- Intégrez les lois fédérales, les réglementations cantonales et les décisions judiciaires pertinentes.\n\n"
                "2. **Clarté et Accessibilité**:\n"
                "- Assurez-vous que vos réponses soient claires et compréhensibles pour un public varié.\n"
                "- Utilisez un langage simple et évitez le jargon technique.\n\n"
                "3. **Identification et Clarification des Ambiguïtés**:\n"
                "- Si la question est ambiguë, demandez des clarifications nécessaires.\n"
                "- Offrez des conseils sur la manière de préciser la question pour obtenir une réponse plus précise.\n\n"
                "4. **Adhérence aux Principes Légaux**:\n"
                "- Respectez strictement les principes de non-discrimination, de transparence et de conformité légale.\n\n"
                "5. **Structure des Réponses**:\n"
                "- Fournissez des explications détaillées et bien structurées.\n"
                "- Incluez les sources et références pertinentes.\n"
                "- Utilisez des exemples pratiques pour illustrer les points importants.\n\n"
                "Voici les sections de contexte que vous devez considérer pour répondre à la question :\n{context}\n\n"
                "Question :\n{users_question}\n\n"
                "Réponse :"
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
    print(answer[:100])

    usd_cost = (tokens_used / 1000000) * 5
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost



######### PLAYGROUND

# question = """Qu'est-ce qu'un bon critère d'évaluation ? quels sont les facteurs et les bases légales ou documentaires supportant cela ?"""


# keywords = [
#     "Adjudication",
#     "Appel d'offres",
#     "Soumissionnaire",
#     "Contrat public",
#     "Transparence",
#     "Non-discrimination",
#     "Concurrence",
#     "Critères d'attribution",
#     "Offre",
#     "Cahier des charges",
#     "Procédure ouverte",
#     "Procédure sélective",
#     "Procédure sur invitation",
#     "Marché public",
#     "Autorité adjudicatrice",
#     "AMP (Accord sur les marchés publics)",
#     "LMP (Loi sur les marchés publics)",
#     "AIMP (Accord intercantonal sur les marchés publics)",
#     "Tribunal administratif fédéral",
#     "Tribunal fédéral",
#     "Recours",
#     "Effet suspensif",
#     "Garantie",
#     "Cautionnement",
#     "Exécution du contrat",
#     "Résiliation",
#     "Dommages-intérêts",
#     "Conditions générales",
#     "Délais",
#     "Publication",
#     "Avis de marché",
#     "Offre économiquement la plus avantageuse",
#     "Critères de sélection",
#     "Critères de qualification",
#     "Évaluation des offres",
#     "Négociation",
#     "Marché de gré à gré",
#     "Marché de services",
#     "Marché de travaux",
#     "Marché de fournitures",
#     "Conformité",
#     "Responsabilité",
#     "Sous-traitance",
#     "Modification de contrat",
#     "Révocation",
#     "Sanctions",
#     "Contrôle",
#     "Audit",
#     "Conflit d'intérêts",
#     "Confidentialité"
# ]


# db_path = r"E:\MP\3. Data base"
# collection = "THEMIS_test"


# models = ollama.list()
# print(models)


# collection, client = initialize_collection(db_path, collection)


# top_chunks = query_chroma_db_qa(collection, question, n_results=15, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"])

# top_chunks = query_chroma_db_qa_keywords(collection, question, n_results=15, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"], keywords=keywords)


# answer = QA(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)

# answer = QA_OLLAMA(question, top_chunks, max_question_tokens=4000, model_name="llama3:latest")

# answer = QA_reformulated(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)

# answer = QA_OG_modified(question, top_chunks, model_name, completion_tokens, max_question_tokens)(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)

