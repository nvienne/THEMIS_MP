import chromadb
from openai import OpenAI
import pandas as pd

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
    distances = response['distances'][0]  # Access the first (and assumed only) list in distances

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

def procurement_assistant(description, additional_info, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=12000):
    client = OpenAI(api_key="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")

    questions = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
    et des informations supplémentaires pertinentes : '{additional_info}', 
    vous devez exploiter votre propre raisonnement et savoir ainsi qu'une base de données exhaustive des lois, ordonnances, documentations officielles et décisions judiciaires relatives aux marchés publics en Suisse 
    pour formuler des questions stratégiques et des directives. 
    Ces éléments doivent porter sur l'analyse de besoin, le système à mettre en place, le cahier des charges, la durabilité et protection de l'environnement, la gestion des risques, le rapport qualité-prix et la notion de qualité. 
    Assurez-vous que les questions et directives sont précises, axées sur l'action et adaptées à la planification et à l'exécution stratégique de l'appel d'offres."""

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

    # Define the pricing
    price_per_million_input_tokens = 5.00  # in USD
    price_per_million_output_tokens = 15.00  # in USD

    input_tokens_phase1 = len(questions.split())
    output_tokens_phase1 = usage_questions.completion_tokens
    total_tokens_phase1 = input_tokens_phase1 + output_tokens_phase1

    # Calculate the cost for phase 1
    cost_input_phase1 = (input_tokens_phase1 / 1_000_000) * price_per_million_input_tokens
    cost_output_phase1 = (output_tokens_phase1 / 1_000_000) * price_per_million_output_tokens
    total_cost_phase1 = cost_input_phase1 + cost_output_phase1

    # Update the return dictionary to include costs
    return {
        "Questions": strategy_questions_guidelines,
        "Total_tokens_phase1": total_tokens_phase1,
        "Total_cost_phase1": total_cost_phase1
    }




# description = """Je dois mener un appel d'offres en procédure ouverte sur du matériel électroménager pour des centres d'hébergement collectifs de migrants. Il s'agira de frigos, lave-linge, sèche-linge, bouilloire, aspirateurs, etc..."""
# additional_info ="""Le développement durable est important, tout comme la capacité à pouvoir livrer rapidement du matériel sur le canton de Genève."""

# db_path = r"E:\MP\3. Data base"
# collection = "THEMIS_test"


# collection, client = initialize_collection(db_path, collection)
# top_chunks = query_chroma_db(collection, description, n_results=15, type=None, juridiction=None, include_data=["documents", "metadatas", "distances"])
# # extracted_info = extract_information(top_chunks)
# answer = procurement_assistant(description, top_chunks, additional_info, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=12000)