# 🧠 Mental Health & Disease Assistant Chatbot with Login & Registration

A complete AI-powered healthcare assistant built using **Streamlit**, **Cohere LLM**, and a **custom medical JSON dataset**, enhanced with **user authentication (Login & Registration)** and automatic chat history storage.

---

## 🔐 User Authentication (Login & Registration)

This project includes a secure login & registration system:

### ✅ **Registration**
- Users create an account with:  
  - Full Name  
  - Email  
  - Username  
  - Password  
- Passwords are securely hashed before storage.
- Saves user credentials in a database (MySQL / Oracle / SQLite based on your configuration).

### ✅ **Login**
- Users log into the chatbot using their email/username + password.
- Invalid credentials show appropriate error messages.
- Once logged in:
  - User sees their previous chat history  
  - New chats are auto-saved under their username

### ✅ **Security**
- Password hashing using SHA256/Bcrypt (depending on your setup)
- No plain-text storage  
- Session-based authentication  

---

## 🧠 Chatbot Features

### 🩺 1. Disease Prediction from Symptoms
Enter natural language symptoms like:
```
I have fever  
my throat hurts  
feeling dizzy  
```
The system uses **Cohere LLM** to classify the correct base disease (strict Option 1 mode).

---

### 🌿 2. AI‑Generated Remedies
After predicting the disease, the bot provides:
- 5+ safe home remedies  
- Clear bullet formatting  
- Line-by-line smooth typing animation  

---

### 💊 3. Medicines & 👨‍⚕️ Doctors (JSON‑Based)
The app loads a large JSON dataset (>1000 lines).

For each disease:
- **Medicines** (common OTC medicines)
- **Doctors** (name, specialization, hospital in Warangal)

---

### 💬 4. Conversational Follow‑Up Flow
After remedies, chatbot asks:
```
Would you like medicine, doctor, or both?
```
You can respond:
- `medicine`
- `doctor`
- `both`

The bot returns info ONLY when requested.

---

### 📚 5. Chat History (Saved Per User)
All chats are stored under:
```
conversations/<username>/<date>.json
```

Users can:
- View past chats
- Load chats from the sidebar
- Continue where they left off

---

### 🔎 6. Sidebar Quick Lookup
Choose any disease to instantly view:
- Medicines  
- Doctors  
- Hospital names  
- Specializations  

No LLM call needed.

---

## 🎨 UI Features
- Clean, dark theme  
- ChatGPT‑style bubbles  
- Sticky top navigation bar  
- Smooth scroll  
- Compact bottom chat input  
- No timestamps  
- Typing animation  
- Responsive layout  

---

## 📁 Project Structure
```
project/
│── app.py
│── login.py
│── register.py
│── db_users.py
│── med_doctors_warangal.json
│── intent_format_1000lines.json
│── conversations/
│── README.md
```

---

## ▶️ How to Run the App
### 1️⃣ Install Dependencies
```
pip install streamlit cohere bcrypt
```

### 2️⃣ Set Cohere API Key
Inside `app.py`:
```
COHERE_API_KEY = "YOUR_API_KEY"
```

### 3️⃣ Start the App
```
streamlit run login.py
```

### 4️⃣ Login → Then chatbot launches automatically

---

## 🔧 Database Setup (MySQL/Oracle/SQLite)

### For MySQL Example:
```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    password_hash TEXT
);
```

Update your DB credentials inside:
- `db_users.py`
- `login.py`
- `register.py`

---

## ⚠️ Disclaimer
This chatbot is for **educational purposes only**.  
It does **not** replace medical diagnosis or professional healthcare advice.

---

## ❤️ Contributions
Feel free to fork, improve, and create PRs!

---

## 📞 Contact
Developed by **Sanjay**  

