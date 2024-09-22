from django.db import models
import pymongo
from datetime import datetime, timezone
from bson import ObjectId
import logging
from django.contrib.auth.hashers import check_password
import ast

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
        self.collection = self.dbname['weather_readings']
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
            result = self.collection.insert_one(reading_data)
            return str(result.inserted_id), 200
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

             result = self.collection.insert_many(weather_list)
             return [str(inserted_id) for inserted_id in result.inserted_ids]
         except Exception as e :
            logging.error(f"Error inserting weather reading: {e}")
            return {"error": "An unexpected error occurred"}, 500
     
     def get_reading(self, reading_id):
         try:
             # covert string ID to ObjectID to match the id in the database
             reading = self.collection.find_one({"_id": ObjectId(reading_id)})
             if reading:
                 reading['_id'] = str(reading['_id']) #convert object id to string
                 return reading, 200
             else:
              return {"success": False, "error": "Weather reading not found"}, 404
         except Exception as e :
             logging.error(f"Error retrieving weather reading: {e}")
             return {"success": False, "error": "An unexpected error occurred"}, 500
             
         #probably does not need this one 
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
                            value = None
                    # If filtering by a temperature range, expect value to be a list or tuple [min, max]
                    if isinstance(value, (list, tuple)) and len(value) == 2:
                        query['Temperature (°C)'] = {'$gte': float(value[0]), '$lte': float(value[1])}
                    elif isinstance(value, (int, float)):
                        query['Temperature (°C)'] = float(value)  # Single temperature value
                elif key == 'Longitude':
                    query['Longitude'] = float(value)
                elif key == 'Device Name':
                    query['Device Name'] = value  
                    pass
          #logging.info(f"Query being executed: {query}")
          readings = self.collection.find(query)
          if readings:
            result = []
            for reading in readings:
                reading['_id'] = str(reading['_id'])  # Convert ObjectId to string
                result.append(reading)
                return result,200
          else:
               return {"error": ' Weather reading not found '},404
          
        except Exception as e:
          logging.error(f"Error fetching weather data: {e}")
        return {"error": "An unexpected error occurred"},500
      
         
     def update_reading(self, reading_id, update_data):
        try:
            # Convert the id to ObjectId
            object_id = ObjectId(reading_id)

            # Fetch the existing document
            existing_data = self.collection.find_one({"_id": object_id})
            if not existing_data:
                return {"error": "Weather reading not found"}, 404

            # Define the correct field names in the database that map to update_data
            field_mapping = {
                "precipitation": "Precipitation mm/h",
                "latitude": "Latitude",
                "longitude": "Longitude",
                "temperature": "temperature (C)",
                "pressure": "Atmospheric Pressure (kPa)",
                "wind_speed": "Max Wind Speed (m/s)",
                "solar_radiation": "Solar Radiation (w/m2)",
                "vapor_pressure": "Vapor Pressure (kPa)",
                "humidity": "Humidity (%)",
                "wind_direction": "Wind Direction (°)"
            }

            # Convert the update_data keys to match the database naming convention
            converted_data = {
                field_mapping.get(key, key): value for key, value in update_data.items()
            }

            # Overwrite the existing document fields with the new data
            for key, value in converted_data.items():
                existing_data[key] = value

            # Update the document using $set to only modify the necessary fields
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": converted_data}
            )

            return {
                "success": result.modified_count > 0,
                "message": "Update successful"
                if result.modified_count > 0 else "No changes made"
            }, 200

        except Exception as e:
            logging.error(f"Error updating weather reading: {e}")
            return {"error": "An unexpected error occurred"},500

    
     def update_readings(self, updates):
        try:
            results = []
            satuts = 200

            field_mapping = {
                "precipitation": "Precipitation mm/h",
                "latitude": "Latitude",
                "longitude": "Longitude",
                "temperature": "temperature (C)",
                "pressure": "Atmospheric Pressure (kPa)",
                "wind_speed": "Max Wind Speed (m/s)",
                "solar_radiation": "Solar Radiation (w/m2)",
                "vapor_pressure": "Vapor Pressure (kPa)",
                "humidity": "Humidity (%)",
                "wind_direction": "Wind Direction (°)"
             }
            
            for update in updates:
                reading_id = update.get('reading_id')
                update_data = update.get('update_data', {})

                if not reading_id:
                    results.append({
                        'reading_id': None,
                        'success': False,
                        'error': 'Missing reading_id',
                        'status': 400
                    })
                    status = 400
                    continue  

                try:
                    object_id = ObjectId(reading_id)
                except Exception as e:
                    results.append({
                        'reading_id': reading_id,
                        'success': False,
                        'error': ' invalid reading id',
                        'status': 400
                    })
                    status = 400
                    continue 

                try:
                   
                    existing_reading = self.collection.find_one({"_id": object_id})
                    
                    if not existing_reading:
                        results.append({
                            'reading_id': reading_id,
                            'success': False,
                            'error': 'Weather reading not found',
                            'status': 404 
                        })
                        status = 404
                        continue  # Skip to the next update if the reading is not found

                    update_data = {
                    field_mapping.get(key, key): value for key, value in update_data.items()
                             }
                    
                    # Remove fields that do not need to be updated
                    update_data.pop('_id', None)
                    update_data.pop('device_name', None)
                    
                    result = self.collection.update_one(
                        {"_id": object_id},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                     results.append({
                        'reading_id': reading_id,
                        'success': True,
                        'message': "Update successful" 
                         
                    })
                    else:
                     results.append({
                        'reading_id': reading_id,
                        'success': False,
                        'message': "No changes made",
                        'status': 400  
                    })
                    status = max(status, 400) 
                    
                except Exception as individual_error:
                    logging.error(f"Error updating weather reading with ID {reading_id}: {individual_error}")
                    results.append({
                        'reading_id': reading_id,
                        'success': False,
                        'error': str(individual_error),
                        'status': 400
                    })
                    status = max(status, 400) 
            
            return results, status
        
        except Exception as e:
            logging.error(f"Error updating multiple weather readings: {e}")
            return {"error": "An unexpected error occurred"}, 500

        
        
     def delete_reading(self, reading_id):
         try:
             object_id = ObjectId(reading_id)
             #delete the reading data from the collection
             result = self.collection.delete_one({"_id": object_id})
             return result.deleted_count > 0
         except Exception as e:
             logging.error(f"Error deleting weather reading: {e}")
             return {"error": "An unexpected error occurred"}, 500
         
     def delete_readings(self, reading_ids):
         try:
             object_ids = [ObjectId(reading_id)for reading_id in reading_ids]
             result = self.collection.delete_many({"_id":{"$in": object_ids}})
             return result.deleted_count# return the number of document that have been deleted 
         except Exception as e:
             logging.error(f"Error deleting multiple weather reading: {e}")
             return 0
             
             
             

             


     
   
			 
     
   
         

              



