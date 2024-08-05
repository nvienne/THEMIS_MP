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
 
def confusion(text, model_name, completion_tokens):
    client = OpenAI(api_key="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")

    messages = [
        {
            "role": "system",
            "content": (
                    """En tant qu'assistant virtuel spécialisé dans l'analyse de dossiers d'appel d'offres pour les marchés publics, votre mission est de soutenir les acheteurs dans la vérification de la clarté de leurs documents. 
                        Veuillez examiner attentivement le texte fourni et analyser les points suivants :\n\n
                        - Ambiguïté des critères d'aptitude :
                        - Les critères de sélection des soumissionnaires ne sont pas clairement définis ou sont trop vagues.
                        - Incohérences dans les délais :
                        - Les dates de soumission, de clarification et de décision finale ne sont pas cohérentes ou sont contradictoires.
                        - Spécifications techniques floues :
                        - Les exigences techniques ne sont pas suffisamment détaillées, laissant place à des interprétations multiples.
                        - Conditions contractuelles ambiguës :
                        - Les termes et conditions du contrat ne sont pas clairement expliqués, notamment en ce qui concerne les pénalités, les garanties et les responsabilités.
                        - Budget et financement non spécifiés :
                        - Le budget alloué au projet ou les modalités de financement ne sont pas clairement indiqués.
                        - Méthodologie d'évaluation non définie :
                        - Les méthodes et les critères d'évaluation des offres ne sont pas clairement expliqués.
                        - Langage technique complexe :
                        - Utilisation de jargon technique sans explication, rendant difficile la compréhension pour les non-spécialistes.
                        - Références à des documents externes :
                        - Références à des normes, des règlements ou des documents externes sans fournir de lien ou de copie.
                        - Manque de clarté sur les livrables :
                        - Les livrables attendus ne sont pas clairement définis ou sont trop généraux.
                        - Incohérences dans les quantités ou les unités de mesure :
                        - Les quantités ou les unités de mesure mentionnées dans les spécifications techniques sont incohérentes ou contradictoires.
                        
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