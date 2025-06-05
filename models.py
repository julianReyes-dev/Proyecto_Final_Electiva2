from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("DB_NAME", "school_management")
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        
        # Collections
        self.users = self.db['users']
        self.teachers = self.db['teachers']
        self.subjects = self.db['subjects']
        self.students = self.db['students']
        self.enrollments = self.db['enrollments']
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        self.users.create_index('username', unique=True)
        self.teachers.create_index('email', unique=True)
        self.students.create_index('student_code', unique=True)
        self.subjects.create_index([('name', 1), ('group', 1), ('career', 1)], unique=True)
    
    def get_db_status(self):
        try:
            # Test the connection
            self.client.admin.command('ping')
            return {
                'connected': True,
                'server_info': self.client.server_info()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

db = Database()