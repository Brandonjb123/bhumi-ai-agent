import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2

DATA_FILE = "rag_data.pkl"

# Muat data yang sudah ada (jika ada)
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
        documents = data.get("documents", [])
        vectorizer = data.get("vectorizer", None)
        doc_vectors = data.get("doc_vectors", None)
else:
    documents = []
    vectorizer = None
    doc_vectors = None

def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump({
            "documents": documents,
            "vectorizer": vectorizer,
            "doc_vectors": doc_vectors
        }, f)

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def add_document(file):
    global documents, vectorizer, doc_vectors

    print(f"[RAG] Memproses file: {file.name}")  # Akan muncul di terminal Streamlit

    if file.name.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    else:
        text = file.read()
        if isinstance(text, bytes):
            text = text.decode('utf-8')

    if not text.strip():
        print("[RAG] Teks kosong setelah ekstrak!")
        return 0

    print(f"[RAG] Teks diekstrak, panjang: {len(text)} karakter")
    documents.append(text)

    # Buat ulang vectorizer dan vektor dokumen
    vectorizer = TfidfVectorizer()
    doc_vectors = vectorizer.fit_transform(documents)

    # Simpan ke file
    save_data()

    print(f"[RAG] Total dokumen sekarang: {len(documents)}")
    return len(documents)

def search(query, n_results=3):
    global vectorizer, doc_vectors, documents
    if not documents or vectorizer is None or doc_vectors is None:
        return {'documents': [[]], 'metadatas': [[]]}

    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, doc_vectors)[0]
    top_indices = np.argsort(similarities)[-n_results:][::-1]

    result_docs = [documents[i] for i in top_indices]
    result_metadatas = [{'source': f'document_{i}.txt', 'chunk': int(i)} for i in top_indices]

    return {
        'documents': [result_docs],
        'metadatas': [result_metadatas]
    }

def clear_documents():
    global documents, vectorizer, doc_vectors
    documents = []
    vectorizer = None
    doc_vectors = None
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)