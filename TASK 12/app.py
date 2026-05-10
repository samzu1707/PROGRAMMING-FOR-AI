import os
import re
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sentence_transformers import SentenceTransformer
import faiss

app = Flask(__name__, template_folder='templates')

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DATA_DIR, 'religion_qa.csv')
EMBED_PATH = os.path.join(DATA_DIR, 'religion_embeddings.npy')
INDEX_PATH = os.path.join(DATA_DIR, 'religion_faiss.index')
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

clean_re = re.compile(r'[^a-zA-Z0-9\s]')


def clean_text(text):
    text = str(text).lower()
    text = clean_re.sub('', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_dataset():
    df = pd.read_csv(CSV_PATH)
    df['question'] = df['question'].astype(str).apply(clean_text)
    df['answer'] = df['answer'].astype(str).apply(str)
    df['combined'] = df['question'] + ' ' + df['answer']
    return df


def build_index(df, model):
    docs = df['combined'].tolist()
    embeddings = model.encode(docs, show_progress_bar=False)
    embeddings = np.array(embeddings, dtype='float32')
    np.save(EMBED_PATH, embeddings)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)
    return index, embeddings


def load_embeddings_index():
    df = load_dataset()
    model = SentenceTransformer(MODEL_NAME)
    if os.path.exists(EMBED_PATH) and os.path.exists(INDEX_PATH):
        embeddings = np.load(EMBED_PATH)
        index = faiss.read_index(INDEX_PATH)
        if embeddings.shape[0] == len(df):
            return df, model, index, embeddings
    return df, model, *build_index(df, model)


df, model, faiss_index, embeddings = load_embeddings_index()

def search_answer(query, top_k=3):
    query_clean = clean_text(query)
    query_emb = model.encode([query_clean]).astype('float32')
    distances, indices = faiss_index.search(query_emb, top_k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(df):
            continue
        similarity = 1.0 / (1.0 + float(dist))
        results.append({
            'question': df.iloc[idx]['question'],
            'answer': df.iloc[idx]['answer'],
            'score': similarity
        })
    return results


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Please provide a question.'}), 400
    results = search_answer(query, top_k=3)
    return jsonify({'query': query, 'results': results})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
