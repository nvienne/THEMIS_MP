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
    print(answer)

    usd_cost = (tokens_used / 1000000) * 5
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost


# question = """Qu'est-ce qu'un bon critère d'évaluation ? quels sont les facteurs et les bases légales ou documentaires supportant cela ?"""


# db_path = r"E:\MP\3. Data base"
# collection = "THEMIS_test"


# collection, client = initialize_collection(db_path, collection)
# top_chunks = query_chroma_db(collection, question, n_results=15, type=None, juridiction="GE", include_data=["documents", "metadatas", "distances"])
# answer = QA(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)