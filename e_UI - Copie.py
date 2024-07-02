import streamlit as st
from openai import OpenAI
from prettytable import PrettyTable
from c_QA import *
from d_Evaluation import *
from f_Criteria_generation import *
from h_Revue import *
from i_ThinkingAssistant import *
from j_Vendor import *
from k_Anonymizer import *

def main():
    st.title("Themis MP")

    # Load your collection or prepare your data
    db_path = r"E:\MP\3. Data base"
    collection_name = "THEMIS_test"
    collection, client = initialize_collection(db_path, collection_name)
    if not collection:
        st.error("Failed to load collection.")
        return
    
    # Selection of functionality
    functionality = st.selectbox("Choisissez la fonctionnalité:", ["Q&A", "Assistant", "Critères", "Revue", "Evaluation", "Synthèse"])

    if functionality == "Q&A":
        handle_qa(collection)
    elif functionality == "Assistant":
        handle_procurement_assistant(collection)
    elif functionality == "Critères":
        handle_criteria_generation()
    elif functionality == "Revue":
        handle_control()
    elif functionality == "Evaluation":
        handle_evaluation()
    elif functionality == "Synthèse":
        handle_synthesis()



def handle_qa(collection):
    # Dropdown for selecting type
    type = st.selectbox("Choisissez le type:", ["Tous", "LEX", "DOC", "ATF"])
    if type == "Tous":
        type = None
        print("type is none")

    # Dropdown for selecting jurisdiction
    jurisdiction = st.selectbox("Choisissez la juridiction:", ["Toutes", "CH", "FR", "GE", "INT", "NE", "VD", "VS"])
    if jurisdiction == "Toutes":
        jurisdiction = None
        print("jurisdiction is none")

    question = st.text_area("Entrez votre question:", "")
    if st.button("Demander", key="qa"):
        model_name = "gpt-4o-2024-05-13"
        completion_tokens = 4000
        max_question_tokens = 8000
        # Passing the selected type and jurisdiction to the query function
        top_chunks = query_chroma_db(collection, question, n_results=15, type=type, juridiction=jurisdiction, include_data=["documents", "metadatas", "distances"])
        answer, usd_cost = QA(question, top_chunks, model_name, completion_tokens, max_question_tokens)
        if answer:
            st.markdown("### Réponse")
            st.write(answer)
            st.markdown("### Sources")
            display_sources(top_chunks)
        else:
            st.error("Aucune réponse reçue.")

def handle_procurement_assistant(collection):
    description = st.text_area("Description de l'objet de l'appel d'offres:", "")
    additional_info = st.text_area("Informations supplémentaires pertinentes:", "")
    
    if st.button("Générer", key="procurement"):
        model_name = "gpt-4o-2024-05-13"
        completion_tokens = 4000
        max_question_tokens = 12000

        top_chunks = query_chroma_db(collection, description, n_results=15, type=None, juridiction=None, include_data=["documents", "metadatas", "distances"])
        results = procurement_assistant(description, top_chunks, additional_info, model_name, completion_tokens, max_question_tokens)
        
        if results:
            st.markdown("### Vue d'ensemble")
            st.write(results["Vue d'ensemble"])
            st.markdown("### Questions Stratégiques et Directives")
            st.write(results["Questions"])
            display_sources(top_chunks)
        else:
            st.error("Aucun résultat reçu.")

def handle_evaluation():
    criteria_name = st.text_input("Nom du critère", "")
    criteria_description = st.text_area("Description du critère", "")
    expected_elements = st.text_area("Éléments attendus", "")
    num_submissions = st.number_input("Nombre de réponses à évaluer", min_value=1, max_value=10, value=3)
    submissions = [st.text_area(f"Soumission {i+1}", "") for i in range(int(num_submissions))]
    if st.button("Évaluer", key="evaluation"):
        evaluations, usd_cost = evaluate_submissions(criteria_name, criteria_description, expected_elements, submissions)
        for idx, evaluation in enumerate(evaluations, start=1):
            st.markdown(f"#### Évaluation de la Réponse {idx}")
            st.write(evaluation)

def handle_criteria_generation():
    description_du_marché = st.text_area("Description du marché", "")
    if st.button("Générer", key="criteria"):
        combined_criteria_content, total_tokens_used, total_usd_cost = run_criteria_generation(description_du_marché)
        if combined_criteria_content:
            st.markdown("### Critères")
            st.write(combined_criteria_content)
        else:
            st.error("Aucune réponse reçue.")

def handle_control():
    text = st.text_area("Entrez le texte de votre document:", "")
    # words_to_anonymize = st.text_area("Entrez les mots/entités à anonymiser (séparés par des virgules):", "").split(',')

    if st.button("Analyser", key="control"):
        # # Anonymize the text
        # anonymized_text, word_to_code, replacement_stats = anonymize_text(text, words_to_anonymize, code_format="[XXX_{}]", case_insensitive=True)

        # Display the anonymized text
        # st.markdown("### Texte Anonymisé")
        # st.write(text)

        # # Display the dictionary of words and codes
        # st.markdown("### Dictionnaire des mots et codes")
        # st.write(word_to_code)

        # # Display the replacement statistics
        # st.markdown("### Statistiques de remplacement")
        # st.write(replacement_stats)

        # Process the anonymized text through the control function
        model_name = "gpt-4o-2024-05-13"
        completion_tokens = 4000  
        report, usd_cost = control(text, model_name, completion_tokens)

        if report:
            st.markdown("### Revue")
            st.write(report)
            # st.markdown(f"**Coût total :** ${usd_cost:.2f}")
        else:
            st.error("Aucune revue reçue.")

def handle_synthesis():
    text = st.text_area("Entrez le texte de votre document:", "")
    # words_to_anonymize = st.text_area("Entrez les mots/entités à anonymiser (séparés par des virgules):", "").split(',')

    if st.button("Synthétiser", key="synthesis"):
        # # Anonymize the text
        # anonymized_text, word_to_code, replacement_stats = anonymize_text(text, words_to_anonymize, code_format="[XXX_{}]", case_insensitive=True)

        # # Display the anonymized text
        # st.markdown("### Texte Anonymisé")
        # st.write(anonymized_text)

        # # Display the dictionary of words and codes
        # st.markdown("### Dictionnaire des mots et codes")
        # st.write(word_to_code)

        # # Display the replacement statistics
        # st.markdown("### Statistiques de remplacement")
        # st.write(replacement_stats)

        # Process the anonymized text through the control function
        model_name = "gpt-4o-2024-05-13"
        completion_tokens = 4000  
        output, usd_cost = synthesis(text, model_name, completion_tokens)

        if output:
            st.markdown("### Synthèse")
            st.write(output)
            # st.markdown(f"**Coût total :** ${usd_cost:.2f}")
        else:
            st.error("Aucune revue reçue.")

def display_sources(top_chunks):
    dataframes = extract_information(top_chunks)
    for doc_type, df in dataframes.items():
        st.markdown(f"### {doc_type}")
        st.table(df)

if __name__ == "__main__":
    main()