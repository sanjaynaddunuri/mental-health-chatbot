import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import bcrypt

# ⚠️ WARNING: Hardcoded credentials are insecure!
# Create a .env file instead: MONGO_URI="your_uri"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://2303a51la4_db_user:Jzf6YuAOYPTNXfdY@capstone.9ee8bg7.mongodb.net/")

class UserDatabase:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client["DocumentVault"]
            self.users = self.db["users"]
            self.users.create_index("username", unique=True)
            print("✅ MongoDB connected!")
        except ConnectionFailure:
            raise Exception("❌ MongoDB connection failed!")
        except Exception as e:
            raise Exception(f"❌ Database error: {e}")

    def register_user(self, username, password):
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            self.users.insert_one({"username": username, "password": hashed, "role": "user"})
            return True, "Registration successful!"
        except DuplicateKeyError:
            return False, "Username already exists!"
        except Exception as e:
            return False, f"Error: {e}"

    def verify_user(self, username, password):
        try:
            user = self.users.find_one({"username": username})
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                return True, user
            return False, None
        except:
            return False, None

    def close(self):
        self.client.close()