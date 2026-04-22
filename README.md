# RAG-based Document Q&A System

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

The **Retrieval-Augmented Generation (RAG) Document Q&A System** allows users to upload documents and query them for relevant information. The system uses advanced techniques like vector search, document embedding, and large language models (LLMs) to provide context-aware, accurate answers based on the content in the documents.

The project integrates with **Pinecone** for vector search and uses **Cohere** or other LLMs for generating the responses to user queries. This system is ideal for handling large documents or knowledge bases and can be integrated into an enterprise solution for automated document-based querying.

## Architecture Diagram
             +---------------------+
             |  User Uploads File   |
             +----------+----------+
                        |
                        v
             +---------------------+
             | Google Drive Search |
             +----------+----------+
                        |
                        v
             +---------------------+
             |  Download Document  |
             +----------+----------+
                        |
                        v
             +---------------------+
             |  Loop Over Items    |
             +----------+----------+
                        |
                        v
        +-------------------------------+
        | Pinecone Vector Store (DB)    |
        +-------------------------------+
                        |
                        v
            +-------------------------+
            | Embedding (Cohere)       |
            +-------------------------+
                        |
                        v
            +-------------------------+
            | RAG Model Response (LLM) |
            +-------------------------+
                        |
                        v
             +-----------------------+
             | Final Answer Display   |
             +-----------------------+



## Features

- **Document Upload:** Upload PDFs or text documents to be indexed.
- **Vector Search:** Indexes documents using Pinecone for efficient search and retrieval.
- **Context-Aware Q&A:** Uses embeddings from Cohere (or any other LLM) for precise, context-aware answers.
- **Automation with n8n:** Uses n8n for workflow automation to integrate Google Drive, Pinecone, and Cohere in a seamless manner.
- **Real-Time Querying:** Allows users to ask questions based on documents uploaded to the system.

## Tech Stack

- **Frontend:**
  - JavaScript (ES6+)
  - HTML/CSS for UI

- **Backend:**
  - Python (Flask or FastAPI for API server)
  - Cohere for embeddings and large language model (LLM) integration
  - Pinecone for vector search and storage
  - n8n for workflow automation

- **Vector Search and Embeddings:**
  - **Pinecone** (Vector Database)
  - **Cohere** (For document embeddings & chat models)

- **Deployment:**
  - Deployed on Vercel for serverless and scalable infrastructure.
  - Integrated with Google Drive for document retrieval.

## Demo

You can interact with the live demo of the **RAG Document Q&A System**:

[**Live Demo**]

## Installation & Setup

Follow these steps to deploy the system locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/anoop2000/RAG-based-Document-Q-A-System.git
   cd RAG-based-Document-Q-A-System

Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install the required dependencies:

pip install -r requirements.txt
Set up Frontend:

Navigate to the frontend directory:

cd frontend

Install the frontend dependencies:

npm install
Google Drive API & Pinecone Setup:
Create a Pinecone account and set up an index.
Set up the Google Drive API to access documents (ensure proper OAuth and permissions).
Run the application:

Start the backend API:

python app.py

Start the frontend development server:

npm start
Open the application in your browser at http://localhost:3000.
How It Works
User Uploads Document: The user uploads a document through the frontend interface (supports PDF, text files).
Document Indexing: The document is then processed by the backend, and the content is embedded using Cohere's API. The embeddings are stored in the Pinecone vector database.
Querying Documents: Users can query the system by typing questions, which are converted into embeddings and matched with the indexed documents in Pinecone.
Generating Answers: The results are then passed through the LLM (Cohere) to generate a human-readable response, which is shown to the user.
Contribution

Feel free to contribute to the project:

Fork the repository.
Create a feature branch (git checkout -b feature-branch).
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new pull request.
License

MIT License. See the LICENSE
 file for more details.
