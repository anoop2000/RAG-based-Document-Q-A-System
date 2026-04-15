import os
import io
import time
import pypdf
import numpy as np
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

# -----------------------------
# CONFIG & PATHS
# -----------------------------
NAMESPACE = "rag-context"

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Pinecone
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    pinecone_index = pc.Index(index_name)
except Exception as e:
    print("WARNING: Pinecone initialization failed. Please check your .env variables:", e)
    pinecone_index = None

app = Flask(__name__)
CORS(app)


# -----------------------------
# TEXT SPLITTING
# -----------------------------
def split_text(text, chunk_size=100):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


# -----------------------------
# GEMINI EMBEDDINGS (BATCH)
# -----------------------------
def get_embeddings(text_list):
    all_embeddings = []

    try:
        batch_size = 5  # 🔥 small batches to avoid overload

        for i in range(0, len(text_list), batch_size):
            batch = text_list[i:i + batch_size]

            response = client.models.embed_content(
                model="models/text-embedding-004",
                contents=batch
            )

            batch_embeddings = [e.values for e in response.embeddings]
            all_embeddings.extend(batch_embeddings)

        print(f"✅ Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    except Exception as e:
        print("❌ Embedding error:", e)
        raise Exception(f"Google Gemini rejected the payload: {str(e)}")

# -----------------------------
# CREATE PINECONE INDEX
# -----------------------------
# def create_index(text):
#     if pinecone_index is None:
#         raise Exception("Pinecone client is not initialized")
        
#     documents = split_text(text)

#     if not documents:
#         return

#     embeddings = get_embeddings(documents)

#     if not embeddings:
#         return
        
#     vectors = []
#     # Build pinecone vectors
#     for i in range(len(documents)):
#         vector_id = str(uuid.uuid4())
#         vectors.append({
#             "id": vector_id,
#             "values": embeddings[i],
#             "metadata": {"text": documents[i]}
#         })

#     # Clear existing document if any before upserting new one
#     try:
#         pinecone_index.delete(delete_all=True, namespace=NAMESPACE)
#     except Exception as e:
#         print("Pinecone delete error during creation:", e)

#     # Upsert to Pinecone in batches
#     for i in range(0, len(vectors), 100):
#         batch = vectors[i:i+100]
#         pinecone_index.upsert(vectors=batch, namespace=NAMESPACE)

def create_index(text):
    if pinecone_index is None:
        raise Exception("Pinecone client is not initialized")
        
    documents = split_text(text)

    if not documents:
        raise Exception("No text chunks created")

    embeddings = get_embeddings(documents)

    if not embeddings or len(embeddings) == 0:
        raise Exception("Embedding generation failed")

    vectors = []
    for i in range(len(documents)):
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embeddings[i],
            "metadata": {"text": documents[i]}
        })

    # Clear old data
    pinecone_index.delete(delete_all=True, namespace=NAMESPACE)

    # Upload
    pinecone_index.upsert(vectors=vectors, namespace=NAMESPACE)

    # 🔥 VERIFY INSERTION
    stats = pinecone_index.describe_index_stats()
    vector_count = stats.get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0)

    if vector_count == 0:
        raise Exception("Vectors not stored in Pinecone")

    print(f"✅ Stored {vector_count} vectors in Pinecone")
    print("📄 Chunks:", len(documents))
    print("🧠 Embeddings:", len(embeddings))
# -----------------------------
# RETRIEVE CONTEXT
# -----------------------------
def retrieve(query, k=2):
    if pinecone_index is None:
        return ""
        
    query_embedding = get_embeddings([query])

    if not query_embedding:
        return ""

    try:
        response = pinecone_index.query(
            vector=query_embedding[0],
            top_k=k,
            include_metadata=True,
            namespace=NAMESPACE
        )
        
        if not response.matches:
            return ""
            
        results = [match.metadata["text"] for match in response.matches if "text" in match.metadata]
        return "\n".join(results)
    except Exception as e:
        print("Pinecone Query Error:", e)
        return ""


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
    file = request.files.get("file")

    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    try:
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

        return jsonify({
            "message": "Document processed and stored successfully"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Upload failed: {str(e)}"}), 500


# 🧹 Clear Document
@app.route("/clear", methods=["POST"])
def clear_document():
    try:
        if pinecone_index is None:
            return jsonify({"message": "Fail: Pinecone client not initialized."}), 500
        pinecone_index.delete(delete_all=True, namespace=NAMESPACE)
        return jsonify({"message": "Document cleared from Pinecone successfully"})
    except Exception as e:
        return jsonify({"message": f"Failed to clear Pinecone: {str(e)}"}), 500


# ❓ Ask Question
@app.route("/ask", methods=["POST"])
def ask():
    try:
        if pinecone_index is None:
            return jsonify({
                "answer": "Server configuration error: Pinecone connection missing."
            })
            
        # Check if Pinecone has any vectors
        stats = pinecone_index.describe_index_stats()
        namespaces = stats.get('namespaces', {})
        if NAMESPACE not in namespaces or namespaces[NAMESPACE].vector_count == 0:
            return jsonify({
                "answer": "Please upload a document first!"
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