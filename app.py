from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
import os

app = Flask(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')

documents = [
    "ZS Sciences is a biopharmaceutical company that discovers, develops, and commercializes therapeutics.",
    "Remdesivir is one of the antiviral medications developed by ZS.",
    "The company focuses on areas like HIV, liver diseases, and oncology.",
    "Paracetamol is commonly used as an analgesic and antipyretic for mild to moderate pain.",
    "Ibuprofen is a non-steroidal anti-inflammatory drug (NSAID) used for treating pain, fever, and inflammation.",
    "Amoxicillin is a penicillin antibiotic used to treat a variety of bacterial infections.",
    # ... Add more as needed
]

doc_embeddings = model.encode(documents, convert_to_numpy=True)

dimension = doc_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(doc_embeddings)

@app.route('/search', methods=['POST'])
def search():
    query = request.json['query']
    query_vec = model.encode([query], convert_to_numpy=True)
    k = 3
    D, I = index.search(query_vec, k)
    results = [documents[i] for i in I[0]]
    return jsonify({'context': results})

def split_into_chunks(text, max_length=500, overlap=100):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = " ".join(current_chunk.split()[-overlap:]) + " " + sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

@app.route('/ingest', methods=['POST'])
def ingest():
    new_text = request.json.get('text')
    if not new_text:
        return jsonify({'error': 'No text provided'}), 400

    new_chunks = split_into_chunks(new_text)

    new_embeddings = model.encode(new_chunks, convert_to_numpy=True)

    global documents, index
    documents.extend(new_chunks)
    index.add(new_embeddings)

    return jsonify({'message': 'Text ingested and chunked', 'chunks_added': len(new_chunks)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)