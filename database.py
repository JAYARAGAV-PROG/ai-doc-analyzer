"""
Database initialization and schema management for AI Document Analyzer
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = Path(__file__).parent / "app.db"


def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Documents table (now with user_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            document_type TEXT,
            document_profile TEXT,
            vector_store_id TEXT,
            UNIQUE(file_path)
        )
    """)
    
    # Single conversation per document (removed conversations table)
    # Messages table now directly references document_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            chunks_used TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")


class Database:
    """Database operations wrapper"""
    
    def __init__(self):
        self.db_path = DB_PATH
        
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Document operations
    def create_document(self, user_id: str, filename: str, file_path: str, 
                       document_type: Optional[str] = None,
                       document_profile: Optional[Dict] = None, 
                       vector_store_id: Optional[str] = None) -> int:
        """Create a new document record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        profile_json = json.dumps(document_profile) if document_profile else None
        
        cursor.execute("""
            INSERT INTO documents (user_id, filename, file_path, document_type, document_profile, vector_store_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, filename, file_path, document_type, profile_json, vector_store_id))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doc_id
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            doc = dict(row)
            if doc['document_profile']:
                doc['document_profile'] = json.loads(doc['document_profile'])
            return doc
        return None
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get all documents for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE user_id = ?
            ORDER BY upload_timestamp DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            doc = dict(row)
            if doc['document_profile']:
                doc['document_profile'] = json.loads(doc['document_profile'])
            documents.append(doc)
        return documents
    
    def update_document_profile(self, doc_id: int, document_type: str, document_profile: Dict):
        """Update document profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        profile_json = json.dumps(document_profile)
        cursor.execute("""
            UPDATE documents 
            SET document_type = ?, document_profile = ?
            WHERE id = ?
        """, (document_type, profile_json, doc_id))
        
        conn.commit()
        conn.close()
    
    # Message operations (directly on document)
    def create_message(self, document_id: int, role: str, content: str, 
                      chunks_used: Optional[List] = None) -> int:
        """Create a new message for a document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        chunks_json = json.dumps(chunks_used) if chunks_used else None
        
        cursor.execute("""
            INSERT INTO messages (document_id, role, content, chunks_used)
            VALUES (?, ?, ?, ?)
        """, (document_id, role, content, chunks_json))
        
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return msg_id
    
    def get_messages_by_document(self, document_id: int) -> List[Dict]:
        """Get all messages for a document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM messages 
            WHERE document_id = ?
            ORDER BY timestamp ASC
        """, (document_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            msg = dict(row)
            if msg['chunks_used']:
                msg['chunks_used'] = json.loads(msg['chunks_used'])
            messages.append(msg)
        return messages


# Initialize database on module import
if __name__ == "__main__":
    init_database()
