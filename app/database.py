from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

class MongoDB:
    def __init__(self):
        # Retrieve environment variables
        self.username = os.getenv("MONGO_USERNAME")
        self.password = os.getenv("MONGO_PASSWORD")

        # Validate that environment variables are set
        if not self.username or not self.password:
            raise ValueError("MongoDB username or password is missing. Please set MONGO_USERNAME and MONGO_PASSWORD.")

        # Construct the MongoDB connection URI
        self.uri = f"mongodb+srv://{self.username}:{self.password}@ivc-cluster.2nmzm9h.mongodb.net/"
        self.client = None

    def connect(self, db_name: str):
        """Connect to the specified database."""
        self.client = MongoClient(self.uri)
        return self.client[db_name]

    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()

# Instantiate the MongoDB class
db = MongoDB()