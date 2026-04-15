import os
import io
import time
import pypdf
import numpy as np
import faiss
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

# -----------------------------
# CONFIG
# -----------------------------
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

# In-memory storage
documents = []
index = None


# -----------------------------
# TEXT SPLITTING
# -----------------------------
def split_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


# -----------------------------
# GEMINI EMBEDDINGS (BATCH)
# -----------------------------
def get_embeddings(text_list):
    try:
        response = client.models.embed_content(
            model="models/embedding-001",
            contents=text_list
        )
        return np.array([e.values for e in response.embeddings])
    except Exception as e:
        print("Embedding error:", e)
        return np.array([])


# -----------------------------
# CREATE FAISS INDEX
# -----------------------------
def create_index(text):
    global documents, index

    documents = split_text(text)

    if not documents:
        return

    embeddings = get_embeddings(documents)

    if embeddings.size == 0:
        return

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    
    # Save to disk to bridge multiple server workers
    try:
        with open("documents.json", "w") as f:
            json.dump(documents, f)
        faiss.write_index(index, "faiss_index.bin")
    except Exception as e:
        print("Failed to write memory to disk:", e)


# -----------------------------
# RETRIEVE CONTEXT
# -----------------------------
def retrieve(query, k=2):
    if index is None:
        return ""

    query_embedding = get_embeddings([query])

    if query_embedding.size == 0:
        return ""

    distances, indices = index.search(query_embedding, k)

    results = [documents[i] for i in indices[0] if i < len(documents)]
    return "\n".join(results)


# -----------------------------
# GENERATE ANSWER (WITH FALLBACK)
# -----------------------------
def generate_answer(context, question):
    prompt = f"""
    Answer ONLY from the context.
    If not found, say "Not found in document".

    Context:
    {context}

    Question:
    {question}
    """

    models = [
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    for model_name in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text

            except Exception as e:
                if "503" in str(e):
                    time.sleep(2 * (attempt + 1))  # retry delay
                else:
                    break

    return "⚠️ All models are busy. Please try again later."


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return "RAG Backend Running ✅"


# 📤 Upload Document
@app.route("/upload", methods=["POST"])
def upload():
    global index, documents

    file = request.files.get("file")

    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    try:
        # 🔥 Reset previous document
        index = None
        documents = []

        if file.filename.lower().endswith('.pdf'):
            pdf_reader = pypdf.PdfReader(io.BytesIO(file.read()))
            text = ""

            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            text = file.read().decode("utf-8")

        if not text.strip():
            return jsonify({"message": "Empty document"}), 400

        create_index(text)

        return jsonify({"message": "Document processed successfully"})

    except Exception as e:
        return jsonify({"message": f"Upload failed: {str(e)}"}), 500


# 🧹 Clear Document
@app.route("/clear", methods=["POST"])
def clear_document():
    global index, documents
    index = None
    documents = []
    
    # Wipe disk persistence
    try:
        if os.path.exists("documents.json"):
            os.remove("documents.json")
        if os.path.exists("faiss_index.bin"):
            os.remove("faiss_index.bin")
    except Exception as e:
        pass
        
    return jsonify({"message": "Document cleared successfully"})


# ❓ Ask Question
@app.route("/ask", methods=["POST"])
def ask():
    try:
        global index, documents

        if index is None:
            # Fallback: Attempt to reload from disk for multi-worker environments
            if os.path.exists("documents.json") and os.path.exists("faiss_index.bin"):
                try:
                    with open("documents.json", "r") as f:
                        documents = json.load(f)
                    index = faiss.read_index("faiss_index.bin")
                except Exception as e:
                    print("Failed to mount from disk:", e)
                    return jsonify({
                        "answer": "Please upload a document first! Server memory was reset."
                    })
            else:
                return jsonify({
                    "answer": "Please upload a document first! Server memory was reset."
                })

        data = request.json
        question = data.get("question")

        if not question:
            return jsonify({"answer": "Please provide a question."})

        context = retrieve(question)
        answer = generate_answer(context, question)

        return jsonify({"answer": answer})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "answer": f"An error occurred on the server: {str(e)}"
        })


# -----------------------------
# RUN SERVER (RENDER SAFE)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)