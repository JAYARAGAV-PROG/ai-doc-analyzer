# Welcome to Your Miaoda Project
Miaoda Application Link URL
    URL:https://medo.dev/projects/app-8jr8pdn33ls1

# AI Document Analyzer - Backend

FastAPI backend with advanced RAG pipeline for document analysis.

## 🏗️ Architecture

```
backend/
├── app.py                  # Main FastAPI application
├── database.py             # SQLite database management
├── pdf_extractor.py        # Multi-fallback PDF extraction
├── rag_pipeline.py         # RAG: chunking, embedding, retrieval
├── document_profiler.py    # Document type and theme identification
├── requirements.txt        # Python dependencies
├── run.sh                  # Startup script
├── uploads/                # Uploaded PDF storage
├── app.db                  # SQLite database (auto-created)
└── chroma_db/              # ChromaDB vector store (auto-created)
```

## 🚀 Quick Start

```bash
# Make script executable
chmod +x run.sh

# Run the backend
./run.sh
```

The server will start at: http://localhost:8000

## 📦 Dependencies

### Core Framework
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **python-multipart**: File upload support

### PDF Processing
- **pdfplumber**: Primary PDF extraction (best for tables)
- **PyMuPDF**: Fallback extraction (good for images)
- **pdfminer.six**: Secondary fallback
- **pytesseract**: OCR fallback for scanned PDFs
- **Pillow**: Image processing

### RAG Pipeline
- **LangChain**: Text chunking and processing
- **sentence-transformers**: Embedding generation (all-mpnet-base-v2)
- **ChromaDB**: Vector database for semantic search

### Utilities
- **httpx**: HTTP client for API calls
- **python-dotenv**: Environment variable management

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory (optional):

```env
# Supabase configuration (for Edge Functions)
VITE_SUPABASE_URL=https://gxnvhgunhyriocbsfgsa.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

### Database

SQLite database (`app.db`) is automatically created with:
- `documents` table: Document metadata and profiles
- `conversations` table: Chat sessions
- `messages` table: User and AI messages

### Vector Store

ChromaDB is automatically initialized in `chroma_db/` directory.
Each document gets its own collection: `doc_{document_id}`

## 📡 API Endpoints

### Health Check
```
GET /
```

### Document Management
```
POST /api/documents/upload
GET /api/documents
GET /api/documents/{doc_id}
```

### Conversation Management
```
POST /api/conversations
GET /api/conversations/{conv_id}
GET /api/documents/{doc_id}/conversations
```

### Query Processing
```
POST /api/query
```

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔍 RAG Pipeline

### 1. Document Processing

```python
# Upload → Extract → Profile → Chunk → Embed → Store

# Extraction fallback chain:
1. pdfplumber (best for structured content)
2. PyMuPDF (good for images)
3. pdfminer (text-only fallback)
4. OCR (for scanned documents)
```

### 2. Document Profiling

Automatically identifies:
- Document type (annual_report, audit_report, legal_document, etc.)
- Main themes (Financial Performance, Risk Management, etc.)
- Purpose and scope
- Key sections

### 3. Embedding Generation

- Model: `sentence-transformers/all-mpnet-base-v2`
- Dimensions: 768
- Chunk size: 1000 characters
- Overlap: 200 characters

### 4. Query Processing

```python
# Query → Expand → Search → Retrieve → Rerank → Synthesize

# Query expansion: 5-6 variations
# Hybrid search: Semantic + keyword
# Retrieval: Top 20 chunks
# Reranking: By similarity to original query
# Selection: Top 3 chunks for context
```

## 🧪 Testing

### Test PDF Extraction

```bash
python pdf_extractor.py path/to/document.pdf
```

### Test RAG Pipeline

```bash
python rag_pipeline.py
```

### Test Document Profiler

```bash
python document_profiler.py
```

### Test Database

```bash
python database.py
```

## 📊 Performance

### Typical Processing Times

- **PDF Upload**: 1-3 seconds
- **Content Extraction**: 2-10 seconds (depends on PDF size and method)
- **Document Profiling**: < 1 second
- **Embedding Generation**: 5-15 seconds (depends on document length)
- **Query Processing**: 2-5 seconds
- **AI Response**: 3-10 seconds (depends on Gemini API)

### Optimization Tips

1. **First Run**: Embedding model download takes ~500MB and 1-2 minutes
2. **Subsequent Runs**: Model is cached, startup is fast
3. **Large Documents**: Consider increasing chunk size for faster processing
4. **Multiple Documents**: Embeddings are generated in parallel where possible

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app:app --port 8001
```

### Module Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Locked

```bash
# Close all connections and restart
rm app.db
python database.py
```

### ChromaDB Errors

```bash
# Reset vector store
rm -rf chroma_db/
# Restart server (will auto-recreate)
```

### OCR Not Working

```bash
# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows:
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

## 🔐 Security Notes

- File uploads are validated (PDF only)
- File paths are sanitized
- Database uses parameterized queries
- CORS is configured for local development
- Production deployment should add authentication

## 📈 Scaling Considerations

For production deployment:
- Use PostgreSQL instead of SQLite
- Deploy ChromaDB as separate service
- Add Redis for caching
- Implement rate limiting
- Add authentication/authorization
- Use cloud storage for PDFs
- Deploy with Docker/Kubernetes

## 🛠️ Development

### Adding New Document Types

Edit `document_profiler.py`:

```python
DOCUMENT_TYPES = {
    'your_type': ['keyword1', 'keyword2', ...]
}
```

### Customizing RAG Parameters

Edit `rag_pipeline.py`:

```python
# Chunk size
chunk_size=1000

# Overlap
chunk_overlap=200

# Retrieval count
top_k=20

# Reranking count
rerank_top_k=3
```

### Changing Embedding Model

Edit `rag_pipeline.py`:

```python
EMBEDDING_MODEL = "sentence-transformers/your-model-name"
```

## 📝 Logs

Logs are output to console. For production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Add type hints
3. Write docstrings
4. Test thoroughly
5. Update documentation

---

**Backend Status**: ✅ Ready for production with proper configuration
