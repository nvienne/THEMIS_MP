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
 
def control(text, model_name, completion_tokens):
    client = OpenAI(api_key="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")

    messages = [
        {
            "role": "system",
            "content": (
                    "En tant qu'assistant virtuel spécialisé dans l'analyse de dossiers d'appel d'offres pour les marchés publics, votre mission est de soutenir les acheteurs dans la vérification de la complétude de leurs documents. Veuillez examiner attentivement le texte fourni et confirmer la présence des informations essentielles suivantes :\n\n"
                    "- Nom et adresse de l'adjudicateur\n"
                    "- Type de marché, type de procédure, codes CPV et CPC\n"
                    "- Description complète des prestations, quantité ou estimation de la quantité, et options disponibles\n"
                    "- Lieu précis et délai d'exécution de la prestation\n"
                    "- Gestion des lots, incluant la limitation du nombre de lots et la possibilité d'offres partielles\n"
                    "- Conditions relatives à la participation des communautés de soumissionnaires et usage de sous-traitants\n"
                    "- Politique sur les variantes: limitation ou exclusion\n"
                    "- Délai annoncé pour la publication du prochain appel d'offres\n"
                    "- Prévisions concernant l'utilisation d'une enchère électronique\n"
                    "- Disposition à engager un dialogue avec les soumissionnaires\n"
                    "- Échéances pour la soumission des offres ou des demandes de participation\n"
                    "- Formalités requises pour la présentation des offres, y compris la séparation des propositions financières et techniques\n"
                    "- Langues admises pour la rédaction des offres\n"
                    "- Détail des critères d'aptitude et des justificatifs à fournir\n"
                    "- Nombre maximal de soumissionnaires invités dans le cadre d'une procédure restreinte\n"
                    "- Critères d'adjudication et leur importance relative\n"
                    "- Possibilité d'attribuer des marchés par lots\n"
                    "- Durée de validité des offres requise\n"
                    "- Modalités d'obtention des documents d'appel d'offres, y compris les coûts associés\n"
                    "- Conformité avec les normes et les accords internationaux\n"
                    "- Identification des soumissionnaires ayant déjà participé\n"
                    "- Recours légaux disponibles en cas de contestation\n\n"
                    "Veuillez analyser le texte suivant et relever explicitement comment chaque point requis est adressé ou mentionné :\n\n"
                    "{text}\n\n"
                    "Rédigez un rapport détaillé indiquant la présence ou l'absence des éléments requis, en fournissant des références spécifiques au texte analysé pour chaque point et en présentant les éléments trouvés."
                    "Finalement, vous listerez les points problématiques."
                )
        },
        {
            "role": "user",
            "content": text  # Direct use of the text input by the user
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

    usd_cost = (tokens_used / 1000000) * 5
    print(f"USD Cost for {tokens_used} tokens: ${usd_cost:.4f}")

    return answer, usd_cost




# text = read_pdf(r"E:\MP\4. Admin\Test_Revue_Synthèse.pdf")
# answer, usd_cost = control(text, model_name="gpt-4o-2024-05-13", completion_tokens=4000)
# print(answer)
# print(usd_cost)