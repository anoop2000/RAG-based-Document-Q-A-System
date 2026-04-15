import React, { useState, useRef } from "react";
import axios from "axios";
import { 
  FileText, UploadCloud, FileCheck, 
  MessageSquare, Loader2, Send, Database, AlertCircle, History, Trash2, X
} from "lucide-react";
import "./style.css";

export default function RAGApp() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [history, setHistory] = useState([]);
  
  const [uploadState, setUploadState] = useState({ status: 'idle', message: '' });
  const [askState, setAskState] = useState({ status: 'idle', message: '' });
  
  const fileInputRef = useRef(null);
  const questionInputRef = useRef(null);

  const BACKEND_URL = "https://rag-based-document-q-a-system-m8xw.onrender.com";

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setUploadState({ status: 'idle', message: '' });
      setAnswer("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadState({ status: 'loading', message: 'Uploading and processing document...' });
    
    // Clear out UI state from previous document QA to avoid confusion
    setQuestion("");
    setAnswer("");
    setHistory([]);
    setAskState({ status: 'idle', message: '' });

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(`${BACKEND_URL}/upload`, formData);
      setUploadState({ status: 'success', message: 'Document processed successfully! Ready for your questions.' });
    } catch (err) {
      const serverMsg = err.response && err.response.data && err.response.data.message;
      setUploadState({ status: 'error', message: serverMsg || err.message || 'Upload failed due to connection error.' });
    }
  };

  const handleClearDocument = async () => {
    try {
      await axios.post(`${BACKEND_URL}/clear`);
    } catch (err) {
      console.warn("Could not clear on backend: ", err);
    }
    
    // Reset all UI states
    setFile(null);
    setUploadState({ status: 'idle', message: '' });
    setQuestion("");
    setAnswer("");
    setAskState({ status: 'idle', message: '' });
    
    // Clear input reference
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    setAskState({ status: 'loading', message: '' });
    setAnswer("");

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { question });
      setAskState({ status: 'success', message: '' });
      setAnswer(res.data.answer);

      console.log("Response:", res.data);
      
      // Update history state
      setHistory(prev => {
        const newHistory = [{ q: question, a: res.data.answer }, ...prev];
        return newHistory.slice(0, 10); // Limit to last 10 entries
      });
    } catch (err) {
      setAskState({ status: 'error', message: err.message || 'Failed to fetch answer.' });
      setAnswer("");
    }
  };

  return (
    <div className="page-wrapper">
      {/* Main Core View Area */}
      <div className="app-container">
        {/* Header */}
        <header className="app-header">
          <h1 className="app-title">
            <Database size={28} className="text-primary" />
            Document Q&A
          </h1>
          <p className="app-subtitle">RAG-powered Knowledge Base</p>
        </header>

        {/* Upload Section */}
        <section className="section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 className="section-title">
              <FileText size={20} />
              1. Provide Context
            </h2>
            {file && (
              <button 
                className="clear-btn" 
                onClick={handleClearDocument}
                style={{
                  background: 'var(--bg-answer)',
                  border: '1px solid var(--border-answer)',
                  borderRadius: '6px',
                  padding: '4px 10px',
                  color: 'var(--text-main)',
                  fontWeight: '500'
                }}
              >
                Clear Document
              </button>
            )}
          </div>
          
          {!file ? (
            <div 
              className="upload-area" 
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={40} className="upload-icon" />
              <p className="upload-text">Click to upload Document</p>
              <p className="upload-hint">Supports PDF and txt files</p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".pdf,.txt"
              />
            </div>
          ) : (
            <div className="file-info">
              <div className="file-name-group">
                <FileCheck size={20} style={{ color: "var(--success)" }} />
                <span>{file.name}</span>
              </div>
              <button 
                className="btn" 
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                onClick={handleUpload}
                disabled={uploadState.status === 'loading' || uploadState.status === 'success'}
              >
                {uploadState.status === 'loading' ? (
                  <><Loader2 size={16} className="spin" /> Processing...</>
                ) : uploadState.status === 'success' ? (
                   <><FileCheck size={16} /> Processed</>
                ) : (
                  <><UploadCloud size={16} /> Process File</>
                )}
              </button>
            </div>
          )}

          {/* Upload Status indicator */}
          {uploadState.message && uploadState.status !== 'loading' && (
            <div className={`status-message status-${uploadState.status}`}>
              {uploadState.status === 'error' ? <AlertCircle size={16} /> : <FileCheck size={16} />}
              {uploadState.message}
            </div>
          )}
        </section>

        {/* Ask Section */}
        <section className="section">
          <h2 className="section-title">
            <MessageSquare size={20} />
            2. Ask a Question
          </h2>
          
          <div className="input-group">
            <div className="input-wrapper">
              <input
                type="text"
                ref={questionInputRef}
                className="text-input"
                placeholder="E.g., What is the main summary of this document?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              />
              {question.length > 0 && (
                <button
                  className="input-clear-btn"
                  onClick={() => {
                    setQuestion("");
                    questionInputRef.current?.focus();
                  }}
                  title="Clear input"
                >
                  <X size={18} />
                </button>
              )}
            </div>
            <button 
              className="btn" 
              onClick={handleAsk}
              disabled={!question.trim() || askState.status === 'loading' || uploadState.status !== 'success'}
              title={uploadState.status !== 'success' ? "Please process a file first" : ""}
            >
              {askState.status === 'loading' ? (
                <><Loader2 size={18} className="spin" /> Generating Answer...</>
              ) : (
                <><Send size={18} /> Ask AI</>
              )}
            </button>
          </div>
        </section>

        {/* Answer Display Section */}
        {answer && (
          <section className="section" style={{ marginTop: '8px' }}>
            <div className="answer-container">
              <div className="answer-header">
                <Database size={18} />
                AI Insights
              </div>
              <div className="answer-text">
                {answer}
              </div>
            </div>
          </section>
        )}
        
        {/* Ask API Error Indicator */}
        {askState.status === 'error' && !answer && (
          <div className="status-message status-error">
            <AlertCircle size={18} />
            {askState.message}
          </div>
        )}
      </div>

      {/* Right Side Panel: History */}
      <aside className="history-panel">
        <div className="history-header">
          <div className="history-title"><History size={18} /> Q&A History</div>
          {history.length > 0 && (
            <button className="clear-btn" onClick={() => setHistory([])} title="Clear history">
              <Trash2 size={16} />
            </button>
          )}
        </div>
        
        {history.length === 0 ? (
          <div className="empty-history">
            No questions asked yet.<br/>Upload a document to get started!
          </div>
        ) : (
          <div className="history-list">
            {history.map((item, idx) => (
              <div 
                key={idx} 
                className="history-item"
                title="Click to view full answer again"
                onClick={() => {
                  setQuestion(item.q);
                  setAnswer(item.a);
                  setAskState({ status: 'success', message: '' });
                }}
              >
                <div className="history-q">{item.q}</div>
                <div className="history-a">{item.a}</div>
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}