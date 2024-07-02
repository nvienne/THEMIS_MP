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

def procurement_assistant(description, top_chunks, additional_info, model_name="gpt-4-1106-preview", completion_tokens=4000, max_question_tokens=12000):
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

    # Phase 1: Generate Overview and Legal Compliance Checklist
    checklist_prompt = f"""Vous êtes un assistant expert en réglementations des marchés publics.

    En tant qu'assistant expert, vous devez fournir un aperçu détaillé du sujet de l'appel d'offres basé sur la description suivante : '{description}'. 
    Cet aperçu doit inclure les points clés, les dimensions stratégiques, les implications opérationnelles et les défis potentiels liés à ce sujet. 
    Utilisez ensuite la base de données suivante pour vous assurer que les documents de l'appel d'offres respectent intégralement le cadre juridique suisse : {context}. 
    Veuillez structurer la revue légale de manière claire et détaillée, en abordant tous les aspects légaux pertinents."""

    checklist_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": checklist_prompt}
        ],
        temperature=0.4,
        max_tokens=completion_tokens
    )

    checklist = checklist_completion.choices[0].message.content

    print("Vue d'ensemble:\n", checklist)

    input_tokens_phase1 = len(checklist_prompt.split())
    output_tokens_phase1 = len(checklist.split())

    # Phase 2: Generate Strategic Questions and Guidelines
    strategy_prompt = f"""Compte tenu de la description de l'objet de l'appel d'offres : '{description}', 
    et des informations supplémentaires pertinentes : '{additional_info}', 
    vous devez exploiter votre propre raisonnement et savoir ainsi qu'une base de données exhaustive des lois, ordonnances, documentations officielles et décisions judiciaires relatives aux marchés publics en Suisse pour formuler des questions stratégiques et des directives. 
    Ces éléments doivent porter sur l'analyse de besoin, le cahier des charges, la gestion des risques, le rapport qualité-prix et la notion de qualité. 
    Assurez-vous que les questions et directives sont précises, axées sur l'action et adaptées à la planification et à l'exécution stratégique de l'appel d'offres."""

    strategy_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": strategy_prompt}
        ],
        temperature=0.5,
        max_tokens=completion_tokens
    )

    strategy_questions_guidelines = strategy_completion.choices[0].message.content

    print("Questions:\n", strategy_questions_guidelines)

    # Calculate tokens used in phase 2
    input_tokens_phase2 = len(strategy_prompt.split())
    output_tokens_phase2 = len(strategy_questions_guidelines.split())

    # Total tokens used
    total_tokens = input_tokens_phase1 + output_tokens_phase1 + input_tokens_phase2 + output_tokens_phase2

    # Calculate the total cost
    total_cost = (total_tokens / 1000) * 0.005

    print(f"Total Tokens Used: {total_tokens}")
    print(f"Total Cost: ${total_cost:.2f}")
    return {"Vue d'ensemble": checklist, "Questions": strategy_questions_guidelines}  




# description = """Je dois mener un appel d'offres en procédure ouverte sur du matériel électroménager pour des centres d'hébergement collectifs de migrants. Il s'agira de frigos, lave-linge, sèche-linge, bouilloire, aspirateurs, etc..."""
# additional_info ="""Le développement durable est important, tout comme la capacité à pouvoir livrer rapidement du matériel sur le canton de Genève."""

# db_path = r"E:\MP\3. Data base"
# collection = "THEMIS_test"


# collection, client = initialize_collection(db_path, collection)
# top_chunks = query_chroma_db(collection, description, n_results=15, type=None, juridiction=None, include_data=["documents", "metadatas", "distances"])
# # extracted_info = extract_information(top_chunks)
# answer = procurement_assistant(description, top_chunks, additional_info, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=12000)