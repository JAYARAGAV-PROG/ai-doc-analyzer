# Login System & Single Conversation Implementation

## ✅ What Was Implemented

### 1. Authentication System
- **Login Page** (`/login`): Beautiful glassmorphism design with sign-in/sign-up tabs
- **Username + Password**: Simulated as `username@miaoda.com` format
- **Email Verification**: Disabled for instant login
- **Auto-sync**: New users automatically synced to profiles table
- **Admin System**: First user becomes admin automatically

### 2. Database Changes

#### Supabase (PostgreSQL)
- Created `profiles` table with `user_role` enum (user/admin)
- Created `handle_new_user()` trigger function
- Set up RLS policies for profile access
- Created `is_admin()` helper function

#### Backend SQLite
- Added `user_id` field to `documents` table
- **Removed** `conversations` table (no longer needed)
- Modified `messages` table to reference `document_id` directly
- Each document now has ONE conversation (all messages linked to document)

### 3. Backend API Changes
- Added JWT token verification via `verify_token()` function
- All endpoints now require authentication (except root `/`)
- Document ownership verification on all operations
- Updated endpoints:
  - `POST /api/documents/upload` - requires auth, links to user
  - `GET /api/documents` - returns only user's documents
  - `GET /api/documents/{doc_id}` - checks ownership
  - `GET /api/documents/{doc_id}/messages` - gets all messages for document
  - `POST /api/query` - requires auth, uses `document_id` directly

### 4. Frontend Changes

#### New Components
- **LoginPage** (`src/pages/LoginPage.tsx`):
  - Sign in / Sign up tabs
  - Username validation (letters, digits, underscores only)
  - Password validation (min 6 characters)
  - Vision Pro glassmorphism design
  - Animated background

#### Updated Components
- **AnalyzerPage** (`src/pages/AnalyzerPage.tsx`):
  - Removed conversation management
  - Messages load directly from document
  - Query sends `document_id` instead of `conversation_id`
  - Added user info display in sidebar
  - Added sign-out button
  
- **LandingPage** (`src/pages/LandingPage.tsx`):
  - Added user profile display in header
  - Added sign-out button
  - Shows current username

- **API Service** (`src/services/api.ts`):
  - Added `getAuthHeaders()` method
  - All requests include JWT token
  - Removed `Conversation` interface
  - Simplified to work with documents only

#### Routing
- **App.tsx**: Enabled `AuthProvider` and `RouteGuard`
- **RouteGuard**: Protects `/analyzer` route
- **Public Routes**: `/`, `/login`, `/403`, `/404`
- Unauthenticated users redirected to `/login`

## 🔐 How It Works

### User Flow
1. User visits app → Redirected to `/login` if not authenticated
2. User signs up → Profile created automatically
3. First user gets `admin` role, others get `user` role
4. User signs in → JWT token stored in Supabase session
5. User uploads document → Linked to their `user_id`
6. User queries document → One continuous conversation per document
7. User can switch between their documents
8. User signs out → Redirected to `/login`

### Authentication Flow
```
Frontend → Supabase Auth → JWT Token
   ↓
Backend receives request with Authorization header
   ↓
Backend verifies token with Supabase
   ↓
Backend extracts user_id from token
   ↓
Backend checks document ownership
   ↓
Backend processes request
```

### Conversation Model
**Before**: Multiple conversations per document
```
Document 1
  ├── Conversation 1 (messages 1-5)
  ├── Conversation 2 (messages 6-10)
  └── Conversation 3 (messages 11-15)
```

**After**: Single conversation per document
```
Document 1
  └── All messages (1-15) directly linked to document
```

## 📝 Database Schema

### Supabase (profiles)
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  username TEXT UNIQUE,
  email TEXT,
  role user_role DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Backend SQLite (documents)
```sql
CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,  -- NEW: Links to Supabase user
  filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  document_type TEXT,
  document_profile TEXT,
  vector_store_id TEXT
);
```

### Backend SQLite (messages)
```sql
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL,  -- CHANGED: Was conversation_id
  role TEXT CHECK(role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  chunks_used TEXT,
  FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

## 🚀 How to Use

### First Time Setup
1. Start backend: `cd backend && ./run.sh`
2. Start frontend: `npm run dev`
3. Visit: http://localhost:5173
4. You'll be redirected to `/login`
5. Click "Sign Up" tab
6. Enter username (letters/digits/underscores only)
7. Enter password (min 6 characters)
8. Click "Sign Up"
9. **You are now the admin!** (first user)

### Regular Usage
1. Sign in with your username and password
2. Upload a PDF document
3. Ask questions - all messages saved to that document
4. Upload another document - separate conversation
5. Switch between documents - each has its own history
6. Sign out when done

## 🔑 Key Features

### Security
- ✅ JWT token authentication
- ✅ Document ownership verification
- ✅ RLS policies on profiles
- ✅ Admin role for first user
- ✅ Password validation

### User Experience
- ✅ Beautiful login page
- ✅ Instant sign-up (no email verification)
- ✅ User info display
- ✅ Easy sign-out
- ✅ One conversation per document (simpler)
- ✅ Persistent chat history

### Technical
- ✅ Clean separation of concerns
- ✅ Type-safe API calls
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive design

## 📊 API Changes Summary

### Removed Endpoints
- ❌ `POST /api/conversations` (no longer needed)
- ❌ `GET /api/conversations/{conv_id}` (no longer needed)
- ❌ `GET /api/documents/{doc_id}/conversations` (no longer needed)

### Modified Endpoints
- ✅ `POST /api/documents/upload` - now requires auth, adds user_id
- ✅ `GET /api/documents` - now returns only user's documents
- ✅ `GET /api/documents/{doc_id}` - now checks ownership
- ✅ `POST /api/query` - now uses document_id instead of conversation_id

### New Endpoints
- ✅ `GET /api/documents/{doc_id}/messages` - get all messages for document

## 🎨 Design Consistency

All components maintain the Vision Pro glassmorphism aesthetic:
- Frosted glass effects (`glass`, `glass-strong`)
- Electric blue primary color
- Soft purple secondary color
- Animated backgrounds
- Smooth transitions
- Glow effects

## ⚠️ Important Notes

1. **First User is Admin**: The very first person to sign up gets admin role
2. **Username Format**: Only letters, digits, and underscores allowed
3. **Password Length**: Minimum 6 characters
4. **Email Verification**: Disabled for instant access
5. **One Conversation**: Each document has one continuous conversation
6. **Backend Required**: FastAPI backend must be running for auth to work
7. **Token Storage**: JWT tokens stored in Supabase session (browser)

## 🐛 Troubleshooting

### "Not authenticated" error
- Make sure you're signed in
- Check if token expired (sign in again)
- Verify backend is running

### "Access denied" error
- You're trying to access someone else's document
- Sign in with the correct account

### Can't sign up
- Username might be taken
- Check username format (no special characters except _)
- Password must be at least 6 characters

### Backend connection failed
- Start the backend: `cd backend && ./run.sh`
- Check if port 8000 is available
- Verify .env file has correct Supabase credentials

## ✨ Summary

The application now has:
1. ✅ Complete authentication system
2. ✅ User-specific document management
3. ✅ Simplified one-conversation-per-document model
4. ✅ Beautiful login page
5. ✅ Secure API with JWT tokens
6. ✅ Admin role for first user
7. ✅ All features working together

**Ready to use!** 🎉
