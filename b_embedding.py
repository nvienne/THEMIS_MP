import pdfplumber
import logging
from PIL import Image
import fitz
import pytesseract
from transformers import XLMRobertaTokenizer, AutoTokenizer, BartTokenizer, BartForConditionalGeneration
import pandas as pd
import re
import logging
import os
from openai import OpenAI
import numpy as np
from tqdm import tqdm
import chromadb
import ast
import json
import tiktoken

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
        {"role": "system", "content": "Tu es un assistant intelligent spécialisé dans la création de résumés précis et exhaustifs de textes de loi. Les résumés doivent être compréhensibles par un public général tout en soulignant les implications légales clés. Utilise des bullet points pour les points saillants lorsqu'approprié."},
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

def process_chunk(chunk, tokenizer, max_tokens=1024, min_tokens=50):
    try:
        """Process a single chunk of text"""
        chunk_tokens = tokenizer.tokenize(chunk)
        if len(chunk_tokens) <= max_tokens:
            return [chunk] if len(chunk_tokens) >= min_tokens else []

        # Split the chunk into smaller chunks
        sub_chunks = []
        for i in range(0, len(chunk_tokens), max_tokens):
            sub_chunk = tokenizer.convert_tokens_to_string(chunk_tokens[i:i + max_tokens])
            sub_chunks.append(sub_chunk.strip())

        return sub_chunks
    except Exception as e:
        logging.error(f"Error in process_chunk function: {e}")
        return []

def chunk_text(text, tokenizer, is_lex=False):
    try:
        paragraphs = re.split(r'\n+', text)
        final_chunks = []
        buffer_chunk = ""
        
        for paragraph in paragraphs:
            if is_lex:
                # For LEX, start a new chunk with "Art." directly
                if paragraph.startswith("Art."):
                    # Process and flush the buffer_chunk if it exists
                    if buffer_chunk:
                        final_chunks.extend(process_chunk(buffer_chunk, tokenizer))
                        buffer_chunk = ""
                    # Directly consider the paragraph as a new chunk
                    buffer_chunk = paragraph
                else:
                    # Accumulate text in buffer_chunk
                    buffer_chunk += ' ' + paragraph if buffer_chunk else paragraph
            else:
                # The existing logic for non-LEX processing
                if re.match(r'\bArt\.\s+[IVXLCDM\d]+', paragraph):
                    if buffer_chunk:
                        final_chunks.extend(process_chunk(buffer_chunk, tokenizer))
                        buffer_chunk = ""
                    final_chunks.extend(process_chunk(paragraph, tokenizer))
                else:
                    buffer_chunk += ' ' + paragraph if buffer_chunk else paragraph
        
        # Process the last buffer_chunk if it exists
        if buffer_chunk:
            final_chunks.extend(process_chunk(buffer_chunk, tokenizer))
        
        return final_chunks
    except Exception as e:
        logging.error(f"Error in chunk_text function: {e}")
        return []

def chunk_text_DOC(text, tokenizer, max_tokens=2500, is_lex=False):
    try:
        paragraphs = re.split(r'\n+', text)
        final_chunks = []
        buffer_chunk = ""
        current_tokens_count = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = tokenizer.tokenize(paragraph)
            paragraph_tokens_count = len(paragraph_tokens)
            
            # Check if adding the paragraph exceeds the token limit
            if current_tokens_count + paragraph_tokens_count > max_tokens:
                # If the buffer is not empty, save it as a chunk
                if buffer_chunk:
                    final_chunks.append(buffer_chunk)
                    buffer_chunk = ""
                    current_tokens_count = 0
                
                # If the paragraph itself is too long, split it further (This part might need more sophisticated handling based on your tokenizer and specific requirements)
                if paragraph_tokens_count > max_tokens:
                    # This is a simplistic split; consider a more nuanced approach for splitting long paragraphs
                    sub_paragraphs = [paragraph[i:i+max_tokens] for i in range(0, len(paragraph), max_tokens)]
                    final_chunks.extend(sub_paragraphs)
                else:
                    # Start a new chunk with the current paragraph
                    buffer_chunk = paragraph
                    current_tokens_count = paragraph_tokens_count
            else:
                # Add paragraph to the buffer
                if buffer_chunk:
                    # Add a space to separate from the previous paragraph if buffer is not empty
                    buffer_chunk += " " + paragraph
                else:
                    buffer_chunk = paragraph
                current_tokens_count += paragraph_tokens_count
        
        # Don't forget to add the last chunk if buffer_chunk is not empty
        if buffer_chunk:
            final_chunks.append(buffer_chunk)
        
        return final_chunks
    except Exception as e:
        logging.error(f"Error in chunk_text function: {e}")
        return []

def process_pdf_files(directory, type_value, jurisdiction_value, model, api_key):
    tokenizer = XLMRobertaTokenizer.from_pretrained('xlm-roberta-base')
    records = []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            text = read_pdf(file_path)
            text = preprocess_text(text)
            chunks = chunk_text(text, tokenizer, is_lex=False)
            summary = generate_summary(text, model, api_key)  
            
            for chunk in chunks:
                records.append({
                    "Filename": filename,
                    "Type": type_value,
                    "Juridiction": jurisdiction_value,
                    "Location": file_path,
                    "Chunk": chunk,
                    "Summary": summary  
                })
    
    df = pd.DataFrame(records)
    db_filename = f"DB_{os.path.basename(directory)}.csv"
    df.to_csv(db_filename, index=False)
    print(f"Data saved to {db_filename}")

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string using TikToken."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def compute_token_counts(csv_path, encoding_name):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Compute the number of tokens for each chunk and store in a new column
    df['Tokens_chunk'] = df['Chunk'].apply(lambda chunk: num_tokens_from_string(chunk, encoding_name) if pd.notnull(chunk) else 0)
    
    # Save the updated DataFrame back to the same CSV file
    df.to_csv(csv_path, index=False)

directory_path = r'E:\MP\1. Documents\ATF'
type_value = "ATF"
jurisdiction_value = 'CH'  
model = "gpt-4-turbo-preview"
api_key="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"
# process_pdf_files(directory_path, type_value, jurisdiction_value, model, api_key)
# compute_token_counts(r"E:\MP\3. Data base\DB.csv", 'cl100k_base')



def add_embeddings_to_csv(csv_path, model_name="text-embedding-ada-002", api_key="YOUR_API_KEY"):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Iterate over rows in DataFrame to generate embeddings
    for index, row in df.iterrows():
        text_to_embed = row['Chunk']  # Adjust column name as needed
        response = client.embeddings.create(model=model_name, input=text_to_embed)
        embedding_vector = response.data[0].embedding
        
        # Convert embedding list to a string for CSV storage
        embedding_string = json.dumps(embedding_vector)
        
        # Add embedding string to new column
        df.at[index, 'Embeddings'] = embedding_string
        print(row)
    
    # Save the updated DataFrame to the original CSV file, effectively replacing it
    df.to_csv(csv_path, index=False)
    
    # Print describe and info of the DataFrame
    print(df.describe())
    print(df.info())

def add_embeddings_for_new_doc(csv_path, model_name="text-embedding-ada-002", api_key="YOUR_API_KEY"):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Check if 'Embeddings' column exists, if not create it
    if 'Embeddings' not in df.columns:
        df['Embeddings'] = None
        print("No Embedding column in csv")
    
    # Iterate over rows in DataFrame to generate embeddings only for new rows without embeddings
    for index, row in df.iterrows():
        # Skip rows that already have embeddings
        if pd.isnull(row['Embeddings']):
            text_to_embed = row['Chunk']  # Adjust column name as needed
            response = client.embeddings.create(model=model_name, input=text_to_embed)
            embedding_vector = response.data[0].embedding
            
            # Convert embedding list to a string for CSV storage
            embedding_string = json.dumps(embedding_vector)
            
            # Add embedding string to new column
            df.at[index, 'Embeddings'] = embedding_string
            print(f"Added embeddings for row {index}")
        else:
            print(f"Skipping row {index}, already has embeddings")

    # Save the updated DataFrame to the same CSV file or a new one if you prefer
    df.to_csv(csv_path, index=False)  # Overwrites the original CSV with updated embeddings
    
    # Print describe and info of the DataFrame
    print(df.describe(include='all'))
    print(df.info())

csv_path = r"E:\MP\3. Data base\DB_LEX.csv"
# add_embeddings_to_csv(csv_path, model_name="text-embedding-ada-002", api_key="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")
# add_embeddings_for_new_doc(csv_path, model_name="text-embedding-ada-002", api_key="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")


def combine_csvs(file_list, columns_to_keep, output_file_name):

    combined_data = []

    for file in file_list:
        df = pd.read_csv(file)
        df = df[columns_to_keep]
        combined_data.append(df)

    # Concatenate all dataframes
    combined_df = pd.concat(combined_data, ignore_index=True)

    # Save the combined dataframe to a new CSV
    combined_df.to_csv(output_file_name, index=False)

file_list = [r"E:\MP\3. Data base\DB_ATF.csv", r"E:\MP\3. Data base\DB_LEX.csv", r"E:\MP\3. Data base\DB_DOC.csv"]
columns_to_keep = ['Filename', 'URL', 'Chunk', 'Embeddings', 'Type', 'Juridiction', 'Summary']
output_file_name = 'DB.csv'
# combine_csvs(file_list, columns_to_keep, output_file_name)




def insert_into_chromadb(csv_path, db_path, collection_name, batch_size=1000):
    df = pd.read_csv(csv_path)
    
    # Ensure embeddings are correctly parsed as lists of floats
    df['Embeddings'] = df['Embeddings'].apply(lambda x: np.array(ast.literal_eval(x)) if pd.notnull(x) else None)
    
    try:
        client = chromadb.PersistentClient(path=db_path)
    except Exception as e:
        print(f"Error initializing the client: {e}")
        return
    
    collection = client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    total_rows = df.shape[0]
    num_batches = (total_rows // batch_size) + (1 if total_rows % batch_size else 0)

    for batch_num in tqdm(range(num_batches), desc="Inserting batches", unit="batch"):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, total_rows)
        
        batch_df = df.iloc[start_idx:end_idx]
        
        embeddings = batch_df['Embeddings'].apply(lambda x: x.tolist() if x is not None else None).tolist()
        chunk = batch_df['Chunk'].tolist()
        filename = batch_df['Filename'].tolist()
        summary = batch_df['Summary'].tolist()
        type = batch_df['Type'].tolist()
        juridiction = batch_df['Juridiction'].tolist()
        url = batch_df['URL'].tolist()

        ids = batch_df.index.astype(str).tolist()

        metadata_list = []
        for e, c, f, t, j, l, s in zip(embeddings, chunk, filename, type, juridiction, url, summary):
            metadata = {
                "chunk": c,
                "type": t,
                "juridiction": j,
                "filename": f,         
                "summary": s ,
                "location": l            
            }
            metadata_list.append(metadata)

        # Debug: Print a sample of the metadata list to verify
        if batch_num == 0:
            print(f"Sample metadata (batch {batch_num + 1}): {metadata_list[:3]}")

        valid_indices = [i for i, emb in enumerate(embeddings) if emb is not None]

        filtered_embeddings = [embeddings[i] for i in valid_indices]
        filtered_metadatas = [metadata_list[i] for i in valid_indices]
        filtered_ids = [ids[i] for i in valid_indices]

        if filtered_embeddings and filtered_metadatas and filtered_ids:
            try:
                collection.add(embeddings=filtered_embeddings, metadatas=filtered_metadatas, ids=filtered_ids)
            except Exception as e:
                print(f"Error adding batch {batch_num + 1} to collection: {e}")
        else:
            print(f"Batch {batch_num + 1}/{num_batches} had no valid embeddings. Skipping.")

    print("Done!")

def inspect_collection(db_path, collection):
    # Initialize ChromaDB PersistentClient
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(collection)

    # 1. Print total number of embeddings in the collection
    total_count = collection.count()
    print(total_count)

    # 2. Peek into the first few embeddings, metadata, and documents
    peek_results = collection.peek(limit=5)
    print(type(peek_results))
    print(peek_results)

    if not isinstance(peek_results, list):
        return

    for record in peek_results:
        if not isinstance(record, dict):
            continue

        print("-" * 50)
        print(f"ID: {record['id']}")
        print(f"Metadata: {record.get('metadatas', {})}")
        print(f"Document: {record.get('documents', {})}")

    # 3. (Optional) Allow user to perform specific queries
    while True:
        action = input("\nDo you want to query the collection? (yes/no): ").lower()
        if action == "yes":
            query_text = input("Enter a document text to find its closest neighbors: ")
            results = collection.query(query_texts=[query_text], n_results=5)
            print("\nTop 5 nearest neighbors for your query:")
            for idx, result in enumerate(results, start=1):
                print(f"\nResult {idx}:")
                print(f"ID: {result['id']}")
                print(f"Distance: {result.get('distances', [None])[0]}")  # Assuming one distance per result
                print(f"Metadata: {result.get('metadatas', {})}")
                print(f"Document: {result.get('documents', {})}")
        elif action == "no":
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

csv_path = r"E:\MP\3. Data base\DB.csv"
db_path = r"E:\MP\3. Data base\Test_25.07.24"
collection = "THEMIS_MP"
insert_into_chromadb(csv_path, db_path, collection, batch_size=1000)
# inspect_collection(db_path, collection)

