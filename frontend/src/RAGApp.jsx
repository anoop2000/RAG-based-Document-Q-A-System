import React, { useState } from "react";
import axios from "axios";

export default function RAGApp() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = "http://127.0.0.1:5000";

  // Upload file
  const handleUpload = async () => {
    if (!file) return alert("Please select a file");

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(`${BACKEND_URL}/upload`, formData);
      alert("✅ Document uploaded!");
    } catch (err) {
      alert("❌ Upload failed");
    }
  };

  // Ask question
  const handleAsk = async () => {
    if (!question) return;

    setLoading(true);

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, {
        question,
      });

      setAnswer(res.data.answer);
    } catch (err) {
      setAnswer("❌ Error fetching answer");
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      <h2>📄 RAG Document Q&A (Vite + React)</h2>

      {/* Upload Section */}
      <div>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={handleUpload}>Upload</button>
      </div>

      <hr />

      {/* Question Section */}
      <div>
        <input
          type="text"
          placeholder="Ask a question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{ width: "300px", padding: "8px" }}
        />

        <button onClick={handleAsk}>Ask</button>
      </div>

      {/* Answer Section */}
      <div style={{ marginTop: "20px" }}>
        {loading ? (
          <p>⏳ Loading...</p>
        ) : (
          <p><b>Answer:</b> {answer}</p>
        )}
      </div>
    </div>
  );
}