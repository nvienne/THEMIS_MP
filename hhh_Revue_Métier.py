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
 
def metier(text, model_name, completion_tokens):
    client = OpenAI(api_key="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")

    messages = [
        {
            "role": "system",
            "content": (
                """En tant qu'assistant virtuel spécialisé dans l'analyse de dossiers d'appel d'offres pour les marchés publics, votre mission est de soutenir les acheteurs dans la vérification de la clarté de leurs documents. 
                Veuillez examiner attentivement le texte fourni et analyser les éléments suivants :\n\n
                - Spécifications techniques :
                  - Quels sont les standards industriels ou les normes spécifiques à respecter pour ce projet ?
                  - Pouvez-vous fournir des exemples de projets similaires réalisés avec succès ?
                - Technologies et outils :
                  - Quelles technologies ou outils spécifiques sont recommandés ou obligatoires pour ce projet ?
                  - Y a-t-il des préférences pour des fournisseurs ou des marques spécifiques ?
                - Intégration et compatibilité :
                  - Comment le nouveau système ou service s'intégrera-t-il avec les systèmes existants ?
                  - Quelles sont les exigences en matière de compatibilité avec les infrastructures actuelles ?
                - Sécurité et conformité :
                  - Quelles sont les exigences en matière de sécurité des données et de conformité réglementaire ?
                  - Y a-t-il des certifications ou des audits de sécurité requis ?
                - Maintenance et support :
                  - Quelles sont les attentes en matière de maintenance et de support post-implémentation ?
                  - Quels sont les SLA (Service Level Agreements) attendus pour le support technique ?
                - Formation et transfert de connaissances :
                  - Y a-t-il des exigences spécifiques pour la formation des utilisateurs finaux et des administrateurs ?
                  - Comment le transfert de connaissances sera-t-il géré ?
                - Gestion de projet :
                  - Quelles sont les méthodologies de gestion de projet préférées ou obligatoires ?
                  - Y a-t-il des jalons ou des livrables spécifiques à respecter ?
                - Évaluation des performances :
                  - Quels sont les KPI (Key Performance Indicators) pour mesurer le succès du projet ?
                  - Comment les performances seront-elles évaluées et rapportées ?
                - Risques et contingences :
                  - Quels sont les principaux risques identifiés pour ce projet et les plans de contingence associés ?
                  - Comment les risques seront-ils gérés et atténués ?
                - Budget et financement :
                  - Y a-t-il des contraintes budgétaires spécifiques à respecter ?
                  - Quelles sont les modalités de paiement et les conditions de facturation ?
                
                Veuillez analyser le texte suivant et relever explicitement comment chaque point requis est adressé ou mentionné :\n\n
                {text}\n\n
                Rédigez un rapport détaillé indiquant la présence ou l'absence des éléments requis, en fournissant des références spécifiques 
                au texte analysé pour chaque point et en présentant les éléments trouvés. 
                Finalement, vous listerez les points problématiques."""
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