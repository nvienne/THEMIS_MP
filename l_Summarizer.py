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

def preprocess_text(text):
    text = text.encode('utf-8', 'replace').decode('utf-8')
    replacements = {"‘": "'", "’": "'", "“": '"', "”": '"'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_summary(text, model="gpt-4-turbo-preview", api_key="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"):
    client = OpenAI(api_key=api_key)
    
    # Prepare the messages for the chat
    messages = [
        {"role": "system", "content": "Tu es un assistant intelligent spécialisé dans la création de résumés précis et exhaustifs de textes de loi. "
        " Les résumés doivent être compréhensibles par un public général tout en soulignant les implications légales clés. Utilise des bullet points pour les points saillants lorsqu'approprié."},
        {"role": "user", "content": f"Je te prie de résumer le texte suivant pour une compréhension générale, en mettant en évidence les principaux éléments légaux et en gardant le résumé concis. Voici le texte: {text}"}
    ]
    
    # Make the API call to create a chat completion
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
        temperature=0.1
    )
    
    # Extract and return the completion text (the summary)
    try:
        summary = completion.choices[0].message.content.strip()
        return summary
    except (IndexError, KeyError) as e:
        print(f"Failed to extract summary. Error: {e}")
        return ""