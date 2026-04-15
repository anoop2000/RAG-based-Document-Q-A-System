import os
import io
import time
import pypdf
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from google import genai

# Load env
load_dotenv()

# Configure Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# In-memory storage
documents = []
index = None


# -----------------------------
# TEXT PROCESSING
# -----------------------------
def split_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def create_index(text):
    global documents, index

    documents = split_text(text)

    if not documents:
        return

    embeddings = embed_model.encode(documents)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))


def retrieve(query, k=2):  # reduced to avoid overload
    if index is None:
        return ""

    query_embedding = embed_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k)

    results = [documents[i] for i in indices[0]]
    return "\n".join(results)


# -----------------------------
# GEMINI WITH FALLBACK + RETRY
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
        for attempt in range(3):  # retry each model 3 times
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text

            except Exception as e:
                if "503" in str(e):
                    time.sleep(2 * (attempt + 1))  # exponential backoff
                else:
                    break  # move to next model

    return "⚠️ All models are busy. Please try again later."


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return "RAG Backend Running ✅"


@app.route("/upload", methods=["POST"])
def upload():
    global index

    file = request.files.get("file")

    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    try:
        global documents
        # Before processing a new document, clear the old one from memory
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

@app.route("/clear", methods=["POST"])
def clear_document():
    global index, documents
    index = None
    documents = []
    return jsonify({"message": "Document cleared successfully"})

@app.route("/ask", methods=["POST"])
def ask():
    try:
        global index

        if index is None:
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
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)