from openai import OpenAI
import pdfplumber
import pdfplumber
import logging
from PIL import Image
import fitz
import pytesseract
from transformers import XLMRobertaTokenizer
import logging
from openai import OpenAI

pytesseract.pytesseract.tesseract_cmd = r"E:\THEMIS\4. Admin\tesseract.exe"


def read_pdf(file):
    with pdfplumber.open(file) as pdf:
        pages = pdf.pages
        text = ''.join(page.extract_text() or '' for page in pages)

    tokenizer = XLMRobertaTokenizer.from_pretrained('xlm-roberta-base')
    tokens = tokenizer.tokenize(text)
    
    if len(tokens) == 0:
        text = pdf_to_text_using_ocr(file)
    else:
        print("file tokenized")
    
    return text

def pdf_to_text_using_ocr(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Identity, colorspace=fitz.csRGB)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        logging.error(f"OCR processing failed for file {file_path}: {e}")
        return ""
 
def synthesis(text, model_name, completion_tokens):
    client = OpenAI(api_key="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")

    messages = [
        {
            "role": "system",
            "content": (
                "Vous êtes un assistant virtuel destiné à guider les soumissionnaires dans l'analyse détaillée des dossiers d'appel d'offres pour les marchés publics. "
                "Votre rôle est de clarifier et de résumer les aspects cruciaux de l'appel d'offres pour assurer une compréhension approfondie et une réponse adéquate de la part du soumissionnaire-utilisateur. "
                "Veuillez évaluer et présenter de manière détaillée les éléments suivants du document d'appel d'offres fourni :\n"
                "- **Description exhaustive du marché :** Décrivez en détail la nature du marché, les services ou produits demandés, et toute spécification qui détaille l'étendue du travail requis.\n"
                "- **Montants :** Indiquez les budgets alloués ou les estimations de coût pour les prestations demandées.\n"
                "- **Durée du contrat et calendrier de l'appel d'offres :** Précisez la période de validité du contrat ainsi que les dates importantes de l'appel d'offres, incluant les délais pour la soumission des propositions.\n"
                "- **Nombre d'adjudicataires :** Mentionnez combien de soumissionnaires seront sélectionnés pour ce marché.\n"
                "- **Nombre de lots et synthèse :** Si applicable, détaillez le découpage du marché en lots et fournissez un résumé des spécifications de chaque lot.\n"
                "- **Détail des critères d'aptitude :** Expliquez les qualifications requises des soumissionnaires, les documents de preuve à fournir et comment ces éléments sont évalués dans le processus de sélection.\n"
                "- **Présentation des critères d'adjudication et leur pondération :** Décrivez les critères selon lesquels les offres seront évaluées, leur importance relative et la méthode de pondération qui influencera la décision finale.\n"
                "- **Les éléments fournis dans le dossier :** Listez les documents et informations que l'adjudicateur a inclus dans le dossier d'appel d'offres pour aider les soumissionnaires à préparer leurs propositions. Faites en des bullet points.\n"
                "- **Les éléments demandés dans l'offre :** Détaillez les documents, attestations, et autres éléments que les soumissionnaires doivent inclure dans leur offre pour qu'elle soit considérée comme complète. Faites en des bullet points.\n\n"
                "Assurez-vous de mettre en lumière tout point qui pourrait nécessiter une attention particulière des soumissionnaires pour augmenter leurs chances de succès."
                "Cette analyse doit servir de base pour aider les soumissionnaires à structurer de manière optimale leur réponse à l'appel d'offres."
                )
            },
        {
            "role": "user",
            "content": text 
        }
    ]

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1,
        max_tokens=completion_tokens
    )

    answer = completion.choices[0].message.content  
    tokens_used = completion.usage.total_tokens 
    print(answer)

    usd_cost = (tokens_used / 1000000) * 10
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost


# text = read_pdf(r"E:\MP\4. Admin\Test_Revue_Synthèse.pdf")
# answer, usd_cost = synthesis(text, model_name="gpt-4-1106-preview", completion_tokens=4000)
# print(answer)
# print(usd_cost)