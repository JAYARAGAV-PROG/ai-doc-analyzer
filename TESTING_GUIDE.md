# Quick Test Guide - Login & Single Conversation

## 🧪 Testing Steps

### Step 1: Start the Application

**Terminal 1 - Backend:**
```bash
cd /workspace/app-8jr8pdn33ls1/backend
./run.sh
```

Wait for:
```
✓ Database initialized
✓ RAG pipeline initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd /workspace/app-8jr8pdn33ls1
npm run dev
```

### Step 2: Test Authentication

1. **Open Browser**: http://localhost:5173
2. **Verify Redirect**: Should automatically redirect to `/login`
3. **See Login Page**: Beautiful glassmorphism design with tabs

### Step 3: Create First User (Admin)

1. Click **"Sign Up"** tab
2. Enter username: `admin` (or any username you like)
3. Enter password: `password123` (or any password 6+ chars)
4. Click **"Sign Up"**
5. **Expected**: 
   - Toast: "Account created! Welcome to AI Document Analyzer"
   - Redirect to `/analyzer`
   - You are now the **admin** (first user)

### Step 4: Test Document Upload

1. **In Analyzer Page**: Click "Upload PDF" button
2. **Select a PDF**: Any business document
3. **Expected**:
   - Upload progress indicator
   - Toast: "Document uploaded successfully"
   - Document appears in sidebar
   - Document is automatically selected

### Step 5: Test Single Conversation

1. **Ask First Question**: "What is this document about?"
2. **Expected**:
   - User message appears immediately
   - Loading indicator while AI processes
   - AI response appears
   - Message saved to database

3. **Ask Follow-up**: "Can you summarize the key points?"
4. **Expected**:
   - New messages added to same conversation
   - All messages visible in chat history
   - Scroll to bottom automatically

5. **Refresh Page**: Press F5
6. **Expected**:
   - Still logged in
   - Document still selected
   - **All messages still there** (persistent)

### Step 6: Test Multiple Documents

1. **Upload Second Document**: Click "Upload PDF" again
2. **Select Different PDF**
3. **Expected**:
   - New document appears in sidebar
   - Automatically selected
   - **Empty chat** (new conversation)

4. **Ask Question**: "What is this about?"
5. **Expected**:
   - New conversation for this document
   - Previous document's messages not shown

6. **Switch Back**: Click first document in sidebar
7. **Expected**:
   - First document selected
   - **Original messages restored**
   - Each document has its own conversation

### Step 7: Test Sign Out

1. **Click Sign Out**: In sidebar or top-right
2. **Expected**:
   - Redirected to `/login`
   - Session cleared

3. **Try to Access Analyzer**: Navigate to http://localhost:5173/analyzer
4. **Expected**:
   - Redirected to `/login`
   - Must sign in again

### Step 8: Test Second User

1. **Sign Up Again**: Different username (e.g., `user2`)
2. **Expected**:
   - Account created
   - Role: **user** (not admin)
   - Empty document list

3. **Upload Document**
4. **Expected**:
   - Document linked to `user2`
   - Not visible to `admin` user

5. **Sign Out and Sign In as Admin**
6. **Expected**:
   - Admin sees only their documents
   - User2's documents not visible

## ✅ Expected Behaviors

### Authentication
- ✅ Unauthenticated users redirected to `/login`
- ✅ Sign up creates account instantly (no email verification)
- ✅ Sign in works with username + password
- ✅ First user gets admin role
- ✅ Subsequent users get user role
- ✅ Sign out clears session

### Documents
- ✅ Each user sees only their own documents
- ✅ Documents linked to user_id
- ✅ Upload requires authentication
- ✅ Document list updates after upload

### Conversations
- ✅ One conversation per document
- ✅ All messages linked directly to document
- ✅ Messages persist across sessions
- ✅ Switching documents shows correct messages
- ✅ No "New Conversation" button (not needed)

### UI/UX
- ✅ User info displayed in sidebar
- ✅ Sign out button accessible
- ✅ Backend connection status indicator
- ✅ Loading states for all operations
- ✅ Error messages for failures
- ✅ Toast notifications for success/error

## 🐛 Common Issues & Solutions

### Issue: "Backend Connection Failed"
**Solution**: 
```bash
cd /workspace/app-8jr8pdn33ls1/backend
./run.sh
```

### Issue: "Not authenticated"
**Solution**: Sign in again (token might have expired)

### Issue: "Access denied"
**Solution**: You're trying to access another user's document

### Issue: Can't see uploaded document
**Solution**: 
- Check if upload succeeded (look for toast)
- Refresh document list
- Check backend logs for errors

### Issue: Messages not persisting
**Solution**:
- Check backend is running
- Check database file exists: `backend/app.db`
- Check browser console for errors

### Issue: Can't sign up
**Solution**:
- Username might be taken (try different one)
- Check username format (only letters, digits, _)
- Password must be 6+ characters

## 📊 Verification Checklist

After testing, verify:

- [ ] Login page loads correctly
- [ ] Sign up creates account
- [ ] First user is admin
- [ ] Sign in works
- [ ] Redirect to analyzer after login
- [ ] Upload requires authentication
- [ ] Documents linked to user
- [ ] Each user sees only their documents
- [ ] One conversation per document
- [ ] Messages persist
- [ ] Switching documents works
- [ ] Sign out works
- [ ] Protected routes redirect to login
- [ ] Backend connection indicator works
- [ ] All toasts show correctly
- [ ] No console errors

## 🎯 Success Criteria

The implementation is successful if:

1. ✅ Users must sign in to access analyzer
2. ✅ Each user has isolated documents
3. ✅ Each document has one continuous conversation
4. ✅ Messages persist across sessions
5. ✅ First user becomes admin
6. ✅ Sign out works properly
7. ✅ No syntax errors
8. ✅ Lint passes
9. ✅ All features work as expected

## 📝 Test Data Suggestions

### Test Users
- `admin` / `password123` (first user)
- `testuser` / `test1234`
- `john_doe` / `secure123`

### Test Documents
- Annual report PDF
- Financial statement PDF
- Legal document PDF
- Any business document PDF

### Test Questions
- "What is this document about?"
- "Summarize the key findings"
- "What are the main themes?"
- "Tell me about the financial performance"
- "What risks are mentioned?"

## 🚀 Ready to Test!

1. Start backend
2. Start frontend
3. Open http://localhost:5173
4. Follow the steps above
5. Verify all features work

**Good luck!** 🎉
