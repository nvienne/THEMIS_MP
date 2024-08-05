from c_QA import *
import pandas as pd
from tqdm import tqdm


keywords = [
    "Adjudication",
    "Appel d'offres",
    "Soumissionnaire",
    "Contrat public",
    "Transparence",
    "Non-discrimination",
    "Concurrence",
    "Critères d'attribution",
    "Offre",
    "Cahier des charges",
    "Procédure ouverte",
    "Procédure sélective",
    "Procédure sur invitation",
    "Marché public",
    "Autorité adjudicatrice",
    "AMP (Accord sur les marchés publics)",
    "LMP (Loi sur les marchés publics)",
    "AIMP (Accord intercantonal sur les marchés publics)",
    "Tribunal administratif fédéral",
    "Tribunal fédéral",
    "Recours",
    "Effet suspensif",
    "Garantie",
    "Cautionnement",
    "Exécution du contrat",
    "Résiliation",
    "Dommages-intérêts",
    "Conditions générales",
    "Délais",
    "Publication",
    "Avis de marché",
    "Offre économiquement la plus avantageuse",
    "Critères de sélection",
    "Critères de qualification",
    "Évaluation des offres",
    "Négociation",
    "Marché de gré à gré",
    "Marché de services",
    "Marché de travaux",
    "Marché de fournitures",
    "Conformité",
    "Responsabilité",
    "Sous-traitance",
    "Modification de contrat",
    "Révocation",
    "Sanctions",
    "Contrôle",
    "Audit",
    "Conflit d'intérêts",
    "Confidentialité"
]


# question_1 = "Quels sont les principaux critères d'évaluation des offres dans une procédure d'appel d'offres selon la Loi fédérale sur les marchés publics (LMP) ?"

# question_2 = """
# Pouvez-vous expliquer en détail les conditions nécessaires pour interrompre une procédure d'adjudication selon l'article 43 de la Loi fédérale sur les marchés publics (LMP) ?
# Cela inclut :
# - Les circonstances spécifiques dans lesquelles une interruption est justifiée.
# - Les étapes procédurales que l'autorité adjudicatrice doit suivre pour interrompre la procédure.
# - Les droits et recours disponibles pour les soumissionnaires en cas d'interruption.
# - Des exemples de situations passées où la procédure a été interrompue et les justifications correspondantes.
# """

# # question_3 = "Quels sont les délais de recours contre une décision d'adjudication et quelles sont les instances compétentes pour traiter ces recours ?"

# question_4 = "Comment la transparence et la non-discrimination sont-elles assurées dans les marchés publics suisses ?"

# question_5 = "Quels sont les éléments obligatoires que doit contenir une annonce de mission pour les travailleurs détachés en Suisse selon l'article 6 de la Loi sur les travailleurs détachés ?"

# question_6 = """
# Pouvez-vous expliquer en détail le rôle et les responsabilités des organes de contrôle cantonaux dans le cadre des marchés publics ?
# Cela inclut :
# - Les principales fonctions et missions de ces organes.
# - La manière dont ils assurent la conformité des procédures de marchés publics avec les réglementations en vigueur.
# - Les mécanismes de contrôle et d'audit qu'ils utilisent pour surveiller les processus d'adjudication.
# - Les sanctions possibles en cas de non-respect des réglementations par les autorités adjudicatrices ou les soumissionnaires.
# - Des exemples de cas où l'intervention des organes de contrôle cantonaux a été cruciale pour garantir la transparence et l'équité dans les marchés publics.
# """


db_path = r"E:\MP\3. Data base"
collection = "THEMIS_test"


collection, client = initialize_collection(db_path, collection)
print("##############")
print("COLLECTION")
print(collection)
print("##############")


# top_chunks_BASE = query_chroma_db_qa(collection, question, n_results=15, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"])

# top_chunks_KEYWORDS = query_chroma_db_qa_keywords(collection, question, n_results=15, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"], keywords=keywords)


# answer_BASE = QA(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)

# answer_OLLAMA = QA_OLLAMA(question, top_chunks, model_name, completion_tokens, max_question_tokens)

# answer_REFORMULATED = QA_reformulated(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)

# answer_OG_MODIFIED = QA_OG_modified(question, top_chunks, model_name, completion_tokens, max_question_tokens)(question, top_chunks, model_name="gpt-4o-2024-05-13", completion_tokens=4000, max_question_tokens=4000)



def evaluate_answers(question, answers, evaluation_model_name, completion_tokens):
    client = OpenAI(api_key="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")
    
    evaluations = []
    for answer in answers:
        messages = [
            {
                "role": "system",
                "content": (
                    "Vous êtes un expert en évaluation de réponses pour les questions sur les marchés publics. "
                    "Veuillez évaluer la réponse suivante sur une échelle de 1 à 10, en fournissant une justification pour votre note.\n\n"
                    f"Question : {question}\n\n"
                    f"Réponse : {answer}\n\n"
                    "Note (entre 1 et 10) :\n"
                    "Justification :"
                )
            },
            {"role": "user", "content": "Évaluez la réponse ci-dessus."}
        ]
        
        completion = client.chat.completions.create(
            model=evaluation_model_name,
            messages=messages,
            temperature=0.2,
            max_tokens=completion_tokens
        )
        
        evaluation = completion.choices[0].message.content.strip()
        
        # Post-process the response to handle various formats
        
        try:
            note, justification = evaluation.split("\nJustification :")
            evaluations.append((note.strip(), justification.strip()))
        except ValueError:
            # Handle the case where the expected format is not met
            note = evaluation.split("\n")[0].strip()
            evaluations.append((note, "Justification not found or format incorrect."))

        # try:
        #     if "Justification :" in evaluation:
        #         note, justification = evaluation.split("Justification :")
        #         note = note.split(":")[1].strip()
        #         evaluations.append((note, justification.strip()))
        #     else:
        #         note = evaluation.split(":")[1].strip()
        #         evaluations.append((note, "Justification not found."))
        # except ValueError:
        #     # Handle the case where the expected format is not met
        #     evaluations.append(("N/A", "Justification not found or format incorrect."))
    
    return evaluations

def run_tests_and_evaluate(questions, qa_functions, collection, completion_tokens):
    results = []
    
    for question in tqdm(questions, desc="Processing questions"):
        top_chunks = query_chroma_db_qa(collection, question, n_results=15, type_filter=None, juridiction_filter=None, include_data=["documents", "metadatas", "distances"])
        
        answers = []
        for qa_function, model_name in qa_functions.items():
            print("##############")
            print("Q&A FUNCTION : ")
            print(qa_function)
            print("##############")
            answer, _ = qa_function(question, top_chunks, model_name=model_name, completion_tokens=completion_tokens, max_question_tokens=4000)
            answers.append(answer)
        
        # Determine the evaluation model name
        evaluation_model_name = "gpt-4o-2024-05-13"

        evaluations = evaluate_answers(question, answers, evaluation_model_name, completion_tokens)

        # Compile results
        for qa_function, (note, justification) in zip(qa_functions.keys(), evaluations):
            results.append({
                "Question": question,
                "QA_Function": qa_function.__name__,
                "Answer": answers[list(qa_functions.keys()).index(qa_function)],
                "Note": note,
                "Justification": justification
            })
    
    return results

def main():
    questions = [
        "Quels sont les principaux critères d'évaluation des offres dans une procédure d'appel d'offres selon la Loi fédérale sur les marchés publics (LMP) ?",
        """
        Pouvez-vous expliquer en détail les conditions nécessaires pour interrompre une procédure d'adjudication selon l'article 43 de la Loi fédérale sur les marchés publics (LMP) ?
        Cela inclut :
        - Les circonstances spécifiques dans lesquelles une interruption est justifiée.
        - Les étapes procédurales que l'autorité adjudicatrice doit suivre pour interrompre la procédure.
        - Les droits et recours disponibles pour les soumissionnaires en cas d'interruption.
        - Des exemples de situations passées où la procédure a été interrompue et les justifications correspondantes.
        """,
        "Quels sont les délais de recours contre une décision d'adjudication et quelles sont les instances compétentes pour traiter ces recours ?",
        "Comment la transparence et la non-discrimination sont-elles assurées dans les marchés publics suisses ?",
        "Quels sont les éléments obligatoires que doit contenir une annonce de mission pour les travailleurs détachés en Suisse selon l'article 6 de la Loi sur les travailleurs détachés ?",
        """
        Pouvez-vous expliquer en détail le rôle et les responsabilités des organes de contrôle cantonaux dans le cadre des marchés publics ?
        Cela inclut :
        - Les principales fonctions et missions de ces organes.
        - La manière dont ils assurent la conformité des procédures de marchés publics avec les réglementations en vigueur.
        - Les mécanismes de contrôle et d'audit qu'ils utilisent pour surveiller les processus d'adjudication.
        - Les sanctions possibles en cas de non-respect des réglementations par les autorités adjudicatrices ou les soumissionnaires.
        - Des exemples de cas où l'intervention des organes de contrôle cantonaux a été cruciale pour garantir la transparence et l'équité dans les marchés publics.
        """
    ]
    
    qa_functions = {
        QA_initial: "gpt-4o-2024-05-13",
        QA_OLLAMA: "llama3:latest",
        QA_reformulated: "gpt-4o-2024-05-13",
        QA_OG_modified: "gpt-4o-2024-05-13"
    }

    db_path = r"E:\MP\3. Data base"
    collection = "THEMIS_test"

    collection, client = initialize_collection(db_path, collection)
    
    completion_tokens = 4000
    
    results = run_tests_and_evaluate(questions, qa_functions, collection, completion_tokens)
    
    # Convert results to DataFrame for easy viewing
    df = pd.DataFrame(results)
    df.to_csv(r"E:\MP\4. Admin\Testing\QAs_comparison.csv")
    print(df)

if __name__ == "__main__":
    main()