
from django.db import models
import pymongo
from datetime import datetime, timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import logging
from bson import ObjectId
import ast
from dateutil import parser 
#import bcrypt
# Create your models here.


class MongoConnection:
    _client = None
    @classmethod
    def get_client(cls):
     if cls._client is None:
        cls._client = pymongo.MongoClient('mongodb+srv://iatlmjax:Tafe2023@webdata.qdvi451.mongodb.net/')
        return cls._client
     
class User:
    def __init__(self):
        #establish connection 
        self.client = MongoConnection.get_client()
        self.dbname = self.client['weather_api_db']
        self.collection = self.dbname['users']

    def update_login(self, username):
        self.collection.update_one(
            {"username": username},
            {"$set": {"lastLogin": datetime.now(timezone.utc)}}
        )
    def login_check(self, username, password, required_role = None):
        try:
            # Fetch user from MongoDB
            user = self.collection.find_one({"username": username})

            if not user:
                return {"error": "Invalid username"}, 401

            # Check the hashed password
            if not check_password(password, user['password']):
                return {"error": "Invalid password"}, 401

            # Check for the required role if specified
            if required_role and user.get('role') != required_role:
                return {"error": f"Unauthorized access: {required_role} role required"}, 403

            # Return the user and success code if everything is valid
            return user, 200
        
        except Exception as e:
            logging.error(f"Error during authentication and authorization: {e}")
            return {"error": "An unexpected error occurred"}, 500

    def insert_user(self, username, password, firstname, lastname, role):
       
        password = make_password(password)
        user_data = {
            "username": username,
            "password": password, #need to be hast with python hash function
            "firstname": firstname,
            "lastname": lastname,
            "create_at": datetime.now(timezone.utc),
            "lastLogin": None,
            "role": role,
            
        }
        # Insert the document into the collection
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)
    
    
    def delete_user(self, user_id):
         try:
             object_id = ObjectId(user_id)
             #delete the reading data from the collection
             result = self.collection.delete_one({"_id": object_id})
             return result.deleted_count > 0
         except Exception as e:
             logging.error(f"Error deleting user: {e}")
             return False
    

    def delete_users(self, filters =None):
         try:
             query = {}
             # apply filter
             if filters:
                 for key, value in filters.items():
                     if key == 'role':
                         #check for role filter
                         query['role'] = value
                     elif key == 'last_login':
                         #check for last login range filter 
                         if isinstance(value, str):
                             try:
                                 value = ast.literal_eval(value)
                             except(ValueError, SyntaxError):
                                 return{"error":"invalid last_login format"}, 400
                         if isinstance(value,(list, tuple)) and len(value) == 2:
                             try:
                                   #parse the start date as timezone-aware UTC datetimes
                                  start_date = parser.isoparse(value[0])
                                  end_date =  parser.isoparse(value[1])
                                    
                                  if start_date >= end_date:
                                    return {"error": "Start date must be earlier than end date"}, 400
                                    
                                  query['lastLogin'] = {'$gte': start_date, '$lte': end_date}
                             except Exception as e:
                              logging.error(f"Error parsing dates: {e}")
                              return {"error": "Invalid date format"}, 400
                     

             result = self.collection.delete_many(query)
             if result.deleted_count > 0:
                return {"message": "User deletes sucessfuly"}, 200
             else:
                return {"error": "No users found within the specified date range"}, 404
         except Exception as e:
             logging.error(f"Error deleting multiple weather reading: {e}")
             return {"error": "An unexpected error occurred"}, 500
    
    def update_user_role(self, date_range, new_role):
        try:

            if not date_range or 'start_date' not in date_range or 'end_date' not in date_range:
                return {"error": "Invalid date range"}, 400
            
            try:
                start_date = parser.isoparse(date_range['start_date'])
                end_date = parser.isoparse(date_range['end_date'])
            except (ValueError, TypeError):
                return {"error": "Invalid date format"}, 400
        
      
            if start_date >= end_date:
             return {"error": "Start date must be earlier than end date"}, 400

            date_query = {
                'create_at': {'$gte': start_date, '$lte': end_date}
            }

            # Perform the update
            result = self.collection.update_many(
                date_query,
                {"$set": {"role": new_role}}
            )

            if result.modified_count > 0:
                return {"message": "User access levels updated successfully"}, 200
            else:
                return {"error": "No users found within the specified date range"}, 404

        except Exception as e:
            logging.error(f"Error updating user access levels: {e}")
            return {"error": "Server issue"}, 500
             
    
