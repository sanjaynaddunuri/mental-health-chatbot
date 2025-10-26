# Mental Health Chatbot (with Login & Registration)

## What this package contains
- `app.py` - Main Streamlit app (login + register + chatbot access)
- `backend.py` - SQLite user management with secure PBKDF2-HMAC-SHA256 password hashing
- `chat.py` - **Your original chatbot file (kept unchanged)**
- `text.json` - Your intents data (copied from upload)
- `pages/Chatbot.py` - Runs `chat.py` after login
- `pages/Login.py`, `pages/Register.py` - Frontend forms
- `requirements.txt` - Dependencies to install

## Important note about `chat.py`
Your uploaded `chat.py` contains an **absolute path** reference to `text.json`:

```py
with open("C:\\Users\\naddu\\Desktop\\text.json", "r") as file:
    return json.load(file)
```

Because `chat.py` is kept exactly as you provided, that line will try to load the JSON from that absolute path on your machine. You have two options to make the chatbot work locally:

1. **Quick — create the file at that absolute path** on your machine and copy `text.json` into it. For Windows, create `C:\Users\naddu\Desktop\text.json`.
2. **Recommended — edit `chat.py` once**: change the `open(...)` path to the relative project path, e.g.:
   ```py
   with open(os.path.join(os.path.dirname(__file__), 'text.json'), 'r') as file:
       return json.load(file)
   ```
   This makes the app portable and GitHub-friendly.

## Run locally (VS Code)
1. Create & activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows (PowerShell)
   source venv/bin/activate   # macOS / Linux
   ```
2. Upgrade pip/build tools and install dependencies:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## GitHub
- Initialize a repo, add files, commit and push as usual.

## Security notes
- Passwords are hashed using PBKDF2-HMAC-SHA256 (150k iterations).
- For production, consider using a proper user management system and HTTPS.
