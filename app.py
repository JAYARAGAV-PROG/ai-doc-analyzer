"""
FastAPI Backend for AI Document Analyzer
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

# Local imports
from database import Database, init_database
from pdf_extractor import extract_pdf_content
from rag_pipeline import get_rag_pipeline
from document_profiler import get_profiler

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Document Analyzer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    logger.info("✓ Database initialized")
    
    # Initialize RAG pipeline (loads embedding model)
    rag = get_rag_pipeline()
    logger.info("✓ RAG pipeline initialized")

# Upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL", "https://gxnvhgunhyriocbsfgsa.supabase.co")
SUPABASE_ANON_KEY = os.getenv("VITE_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4bnZoZ3VuaHlyaW9jYnNmZ3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5MzYwOTMsImV4cCI6MjA4MjUxMjA5M30.Ntxtg5MqN5qjydZDoCiIRof4Lp9RmrW6kGnXzbJmdzc")

# Database instance
db = Database()


# Helper function to verify JWT token
async def verify_token(authorization: str = Header(None)) -> str:
    """Verify JWT token and return user_id"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(' ')[1]
    
    # Verify token with Supabase
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Token verification failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_data = response.json()
        return user_data['id']


# Pydantic models
class QueryRequest(BaseModel):
    document_id: int
    query: str
    intent: Optional[str] = "fact"


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str


# API Endpoints

@app.get("/")
async def root():
    return {"message": "AI Document Analyzer API", "status": "running"}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), authorization: str = Header(None)):
    """
    Upload and process a PDF document (requires authentication)
    """
    try:
        # Verify user
        user_id = await verify_token(authorization)
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save file
        file_path = UPLOAD_DIR / f"{datetime.now().timestamp()}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        
        # Extract PDF content
        logger.info("Extracting PDF content...")
        extraction_result = extract_pdf_content(str(file_path))
        
        if not extraction_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"PDF extraction failed: {extraction_result.get('error', 'Unknown error')}"
            )
        
        # Create document record with user_id
        doc_id = db.create_document(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path)
        )
        
        logger.info(f"Document record created: {doc_id}")
        
        # Generate document profile
        logger.info("Generating document profile...")
        profiler = get_profiler()
        profile = profiler.profile_document(extraction_result['text'], file.filename)
        
        # Update document with profile
        db.update_document_profile(
            doc_id=doc_id,
            document_type=profile['document_type'],
            document_profile=profile
        )
        
        # Store in ChromaDB
        logger.info("Storing document in vector database...")
        rag = get_rag_pipeline()
        vector_store_id = rag.store_document(
            doc_id=doc_id,
            text=extraction_result['text'],
            metadata={
                'filename': file.filename,
                'document_type': profile['document_type'],
                'user_id': user_id
            }
        )
        
        logger.info(f"✓ Document processed successfully: {doc_id}")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "pages": extraction_result['pages'],
            "extraction_method": extraction_result['method'],
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents(authorization: str = Header(None)):
    """Get all documents for the authenticated user"""
    try:
        user_id = await verify_token(authorization)
        documents = db.get_user_documents(user_id)
        return {"success": True, "documents": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int, authorization: str = Header(None)):
    """Get document by ID (must belong to user)"""
    try:
        user_id = await verify_token(authorization)
        document = db.get_document(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership
        if document['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {"success": True, "document": document}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/messages")
async def get_document_messages(doc_id: int, authorization: str = Header(None)):
    """Get all messages for a document"""
    try:
        user_id = await verify_token(authorization)
        document = db.get_document(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership
        if document['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        messages = db.get_messages_by_document(doc_id)
        
        return {
            "success": True,
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def query_document(request: QueryRequest, authorization: str = Header(None)):
    """
    Query a document and get AI-generated response
    """
    try:
        # Verify user
        user_id = await verify_token(authorization)
        
        # Get document and verify ownership
        document = db.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Save user message
        db.create_message(
            document_id=request.document_id,
            role="user",
            content=request.query
        )
        
        # Get RAG pipeline
        rag = get_rag_pipeline()
        
        # Retrieve relevant chunks using the correct method
        logger.info(f"Retrieving context for query: {request.query}")
        chunks = rag.retrieve_context(
            doc_id=request.document_id,
            query=request.query,
            intent="fact"  # Default intent
        )
        
        # Check if we got any chunks
        if not chunks:
            logger.warning(f"No chunks found for document {request.document_id}")
            # Still provide a response, but note the limitation
            context = "No specific content found in the document for this query."
        else:
            # Build context
            context = "\n\n".join([chunk['text'] for chunk in chunks])
        
        document_profile = document.get('document_profile', {})
        
        # Parse document_profile if it's a JSON string
        if isinstance(document_profile, str):
            import json
            try:
                document_profile = json.loads(document_profile)
            except:
                document_profile = {}
        
        # Prepare prompt for Gemini
        system_prompt = f"""You are an AI assistant specialized in analyzing business documents.

Document Information:
- Type: {document_profile.get('document_type', 'Unknown')}
- Purpose: {document_profile.get('purpose', 'Not specified')}
- Key Themes: {', '.join(document_profile.get('themes', []))}

Relevant Context from Document:
{context}

Instructions:
- Answer the user's question based on the document content provided
- Be natural and conversational
- If the answer isn't in the context, say so politely
- Provide specific details when available
"""
        
        # Call Gemini Edge Function
        logger.info("Calling Gemini API...")
        
        # Format the request in Gemini API format
        # Combine system prompt and user query into a single user message
        combined_prompt = f"{system_prompt}\n\nUser Question: {request.query}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{SUPABASE_URL}/functions/v1/gemini-chat",
                headers={
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": combined_prompt}]
                        }
                    ]
                }
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Gemini API error: {error_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Gemini API error: {error_text}"
                )
            
            # Parse SSE stream response
            assistant_response = ""
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        import json
                        data = json.loads(line[6:])
                        if 'candidates' in data and len(data['candidates']) > 0:
                            candidate = data['candidates'][0]
                            if 'content' in candidate and 'parts' in candidate['content']:
                                for part in candidate['content']['parts']:
                                    if 'text' in part:
                                        assistant_response += part['text']
                    except json.JSONDecodeError:
                        continue
            
            if not assistant_response:
                assistant_response = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        
        # Save assistant message
        db.create_message(
            document_id=request.document_id,
            role="assistant",
            content=assistant_response,
            chunks_used=[chunk['id'] for chunk in chunks] if chunks else []
        )
        
        logger.info("✓ Query processed successfully")
        
        return {
            "success": True,
            "response": assistant_response,
            "chunks_used": len(chunks) if chunks else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
