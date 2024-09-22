from django.db import models
import pymongo
from datetime import datetime, timezone
from dateutil import parser 
from bson import ObjectId
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


    
class Station:
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
        
    def get_readings(self, filters=None):
        try:
          query = {}
        # Apply filters
          if filters:
            for key, value in filters.items():
                if key == 'Temperature':
                    if isinstance(value, str):
                        try:
                            value = ast.literal_eval(value)
                        except (ValueError, SyntaxError):
                            return {f"Invalid temperature for filtering: {value}"}, 400
                    # If filtering by a temperature range, expect value to be a list or tuple [min, max]
                    if isinstance(value, (list, tuple)) and len(value) == 2:
                        query['Temperature (°C)'] = {'$gte': float(value[0]), '$lte': float(value[1])}
                    elif isinstance(value, (int, float)):
                        query['Temperature (°C)'] = float(value)  # Single temperature value 
                    else:
                        return {"error": "Invalid temperature format"}, 400
                    
        
          readings = self.weather_collection.find(query)
          result = []
          for reading in readings:
                reading['_id'] = str(reading['_id'])  # Convert ObjectId to string
                result.append(reading)
          if result:
                return result,200
          else:
               return {"error": "Weather reading not found"},404
          
        except Exception as e:
          logging.error(f"Error fetching weather data: {e}")
        return {"error": "An unexpected error occurred"},500
    
    def insert_reading(self, device_name, latitude, longitude, temperature, pressure, wind_speed, solar_radiation, vapor_pressure, humidity, wind_direction, precipitation):
        """Insert a new weather reading into the database."""
        reading_data = {
            "Device Name":device_name,
            "Precipitation mm/h": precipitation,
            "Time": datetime.now(),  # Ensure UTC timestamp
            "Latitude": latitude,
            "Longitude": longitude,
            "temperature (C)": temperature,
            "Atmospheric Pressure (kPa)": pressure,
            "Max Wind Speed (m/s)": wind_speed,
            "Solar Radiation (w/m2)": solar_radiation,
            "Vapor Pressure (kPa)": vapor_pressure,
            "Humidity (%)": humidity,
            "Wind Direction (°)": wind_direction
        }

        try:
            result = self.weather_collection.insert_one(reading_data)
            return str(result.inserted_id), 201
        except Exception as e:
            logging.error(f"Error inserting weather reading: {e}")
            return {"error": "An unexpected error occurred"}, 500
            
     
    def insert_multiple_reading(self, weathers):
         # Preapre a list of weather documents

         weather_list = []
         for weather in weathers:
             device_name = weather.get('device_name')
             precipitation = weather.get('precipitation')
             latitude = weather.get('latitude')
             longitude = weather.get('longitude')
             temperature = weather.get('temperature')
             pressure = weather.get('pressure')
             wind_speed = weather.get('wind_speed')
             solar_radiation = weather.get('solar_radiation')
             vapor_pressure = weather.get('vapor_pressure')
             humidity = weather.get('humidity')
             wind_direction = weather.get('wind_direction')
             

             weather_list.append({
              "Device Name":device_name,
              "Precipitation mm/h": precipitation,
              "Time": datetime.now(), 
              "Latitude": latitude,
              "Longitude": longitude,
              "temperature (C)": temperature,
              "Atmospheric Pressure (kPa)": pressure,
              "Max Wind Speed (m/s)": wind_speed,
              "Solar Radiation (w/m2)": solar_radiation,
              "Vapor Pressure (kPa)": vapor_pressure,
              "Humidity (%)": humidity,
              "Wind Direction (°)": wind_direction

             })
            
         try:

             result = self.weather_collection.insert_many(weather_list)
             return [str(inserted_id) for inserted_id in result.inserted_ids], 200
         except Exception as e :
            logging.error(f"Error inserting weather reading: {e}")
            return {"error": "An unexpected error occurred"}, 500
     
