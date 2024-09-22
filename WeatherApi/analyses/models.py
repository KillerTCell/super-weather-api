from django.db import models
import pymongo
from datetime import datetime, timezone
from dateutil import parser, relativedelta
import logging
from django.contrib.auth.hashers import check_password
import ast
from pymongo import DESCENDING

#import bcrypt
# Create your models here.



class MongoConnection:
    _client = None
    @classmethod
    def get_client(cls):
     if cls._client is None:
        cls._client = pymongo.MongoClient('mongodb+srv://iatlmjax:Tafe2023@webdata.qdvi451.mongodb.net/')
        return cls._client

    
class WeatherReading:
    def __init__(self):
        #establish connection 
        self.client = MongoConnection.get_client()
        self.dbname = self.client['weather_api_db']
        self.weather_collection = self.dbname['weather_readings']
        self.user_collection = self.dbname['users']



    def update_login(self, username):
        self.user_collection.update_one(
            {"username": username},
            {"$set": {"lastLogin": datetime.now(timezone.utc)}}
        )

    def login_check(self, username, password, required_role = None):
        try:
            # Fetch user from MongoDB
            user = self.user_collection.find_one({"username": username})

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
        
    def find_max_temperature(self, filters=None):
     try:
            query = {}
            date_range = False

            # Extract and parse the date range from filters
            if filters:
                for key, value in filters.items():
                    if key == 'Date_range':
                        if isinstance(value, str):
                            try:
                                value = ast.literal_eval(value)
                            except (ValueError, SyntaxError):
                                value = None
                        if isinstance(value, (list, tuple)) and len(value) == 2:
                            try:
                                start_date = parser.isoparse(value[0])
                                end_date = parser.isoparse(value[1])
                                if start_date <= end_date:
                                    query['Time'] = {'$gte': start_date, '$lte': end_date}
                                    date_range = True
                            except Exception as e:
                                logging.error(f"Error: {e}")

            if not date_range:
                return {"error": "Invalid date range or no data found for the given date range"}, 400

            # Query to find the max temperature within the given date range
            max_temp= self.weather_collection.find(query).sort("Temperature (°C)", DESCENDING).limit(1)

            # Check if any data is found if not return error 
            max_temp_list = list(max_temp)
            if len(max_temp_list) == 0:
                return {"error": "No data found for the given date range"}, 404

            #convert doc to dictionary 
            result = max_temp_list[0]
            result['_id'] = str(result['_id'])

            return {
                "Sensor Name": result.get("Device Name"),
                "Reading Date/Time": result.get("Time"),
                "Temperature (°C)": result.get("Temperature (°C)")
            }, 200

     except Exception as e:
        logging.error(f"Error finding max temperature: {e}")
        return {"error": "An unexpected error occurred"}, 500
    
    def find_weather_by_station(self, filters=None):
        try:
            query = {}
            if filters:
                for key, value in filters.items():
                    if key == 'Device Name':  
                        try:
                            device_exist = self.weather_collection.find_one({"Device Name": value})

                            if device_exist:
                                query['Device Name'] = value
                            else:
                                return {"error": "Device name not found"}, 404
                        except Exception as e:
                            logging.error(f"Error finding device name: {e}")
                            return {"error": "Internal server error"}, 500
                    
                    elif key == 'Time':
                        try: 
                            query['Time'] = parser.isoparse(value)  
                        except (ValueError, parser.ParserError):
                            return {"error": "Invalid time format"}, 400

            # Fields to be retrieved
            retrieve_data = {
                "Temperature (°C)": 1,
                "Atmospheric Pressure (kPa)": 1,
                "Solar Radiation (W/m2)": 1,
                "Precipitation mm/h": 1,
                "_id": 0
            }
            weather_data = self.weather_collection.find_one(query, retrieve_data)
            # Check if any data was found
            if weather_data:
                return weather_data, 200
            else:
                return {"error": "No record found for the given date/time"}, 404

        except Exception as e:
            logging.error(f"Error fetching weather data: {e}")
            return {"error": "An unexpected error occurred"}, 500

    def find_max_precipitation(self, filters=None):
        try:
            query = {}
            date_valid = True  
            if filters:
                for key, value in filters.items():
                    if key == 'Device Name':  
                        try:
                            device_exist = self.weather_collection.find_one({"Device Name": value})

                            if device_exist:
                                query['Device Name'] = value  
                            else:
                                return {"error": "Device name not found"}, 404 
                        except Exception as e:
                            logging.error(f"Error finding device name: {e}")
                            return {"error": "Internal server error"}, 500 

                    elif key == 'Time':
                       try:
                            end_date = parser.isoparse(value)
                            start_date = end_date - relativedelta(months=5)
                            query['Time'] = {'$gte': start_date, '$lte': end_date}
                       except (ValueError, parser.ParserError):
                            logging.error(f"Date parsing error: ")
            if not date_valid:
                return {"error": "Invalid date format"}, 400  

            max_precipitation = self.weather_collection.find(query).sort("Precipitation mm/h", DESCENDING).limit(1)

            max_precipitation_list = list(max_precipitation)
            if len(max_precipitation_list) == 0:
                return {"error": "No record found for the given date/time"}, 404

            # Extract the result
            result = max_precipitation_list[0]
            result['_id'] = str(result['_id'])  
            
            return {
                "Device Name": result.get("Device Name"),
                "Time": result.get("Time"),
                "Precipitation mm/h": result.get("Precipitation mm/h"),
            }, 200

        except Exception as e:
            logging.error(f"Error fetching max precipitation: {e}")
            return {"error": "An unexpected error occurred"}, 500

                
        


                    