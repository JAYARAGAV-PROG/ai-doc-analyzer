# ⚠️ IMPORTANT: Backend Server Required

## The Error You're Seeing

**"Upload failed - Failed to fetch"** means the FastAPI backend server is **not running**.

The frontend (React app) is running, but it cannot connect to the backend API at `http://localhost:8000`.

## ✅ Solution: Start the Backend Server

### Option 1: Quick Start (Recommended)

Open a **NEW terminal window** and run:

```bash
cd /workspace/app-8jr8pdn33ls1/backend
chmod +x run.sh
./run.sh
```

Wait for these messages:
```
✓ Database initialized
✓ Embedding model loaded
✓ RAG pipeline initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Option 2: Manual Start

If the script doesn't work, run manually:

```bash
cd /workspace/app-8jr8pdn33ls1/backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 🔍 Verify Backend is Running

1. **Check the terminal** - You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Test in browser** - Open: http://localhost:8000
   - You should see: `{"message":"AI Document Analyzer API","status":"running"}`

3. **Check API docs** - Open: http://localhost:8000/docs
   - You should see the interactive API documentation

## 🚀 Once Backend is Running

1. Go back to your frontend: http://localhost:5173
2. Click "Upload Document"
3. Select a PDF file
4. The upload should now work!

## 🐛 Troubleshooting

### "Port 8000 already in use"

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process (replace PID with actual number)
kill -9 <PID>

# Or use a different port
uvicorn app:app --port 8001
# Then update .env: VITE_API_URL=http://localhost:8001
```

### "Module not found" errors

```bash
cd /workspace/app-8jr8pdn33ls1/backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Python not found"

```bash
# Check Python version (need 3.9+)
python3 --version

# If not installed, install Python 3.9 or higher
```

### First Run Takes Longer

The first time you start the backend:
- It downloads the embedding model (~500MB)
- This takes 1-2 minutes
- Subsequent starts are much faster

## 📋 Complete Startup Checklist

- [ ] Backend terminal open
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Backend running on port 8000
- [ ] Can access http://localhost:8000
- [ ] Frontend running on port 5173
- [ ] Can access http://localhost:5173
- [ ] Upload works without "Failed to fetch" error

## 💡 Pro Tip

Keep **two terminal windows** open:
1. **Terminal 1**: Backend server (runs continuously)
2. **Terminal 2**: Frontend dev server (runs continuously)

Both need to be running for the application to work!

---

**Need more help?** See QUICKSTART.md or README.md for detailed instructions.
