from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import check_password
from .models import  WeatherReading
from bson import ObjectId
import logging

# Create your views here.
@csrf_exempt
def reading(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            login_username = data.get('username')
            login_password = data.get('password')

            device_name = data.get('device_name')
            precipitation = data.get('precipitation')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            temperature = data.get('temperature')
            pressure = data.get('pressure')
            wind_speed = data.get('wind_speed')
            solar_radiation = data.get('solar_radiation')
            vapor_pressure = data.get('vapor_pressure')
            humidity = data.get('humidity')
            wind_direction = data.get('wind_direction')
           
            if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)
            
            weather_model = WeatherReading()
            weather_model.update_login(login_username)
            user_data, status = weather_model.login_check(login_username, login_password, required_role='Teacher')
            

            if status != 200:
                return JsonResponse(user_data, status=status)
            
            
            required_fields = [device_name, precipitation,latitude,longitude,temperature,pressure,wind_speed,solar_radiation,vapor_pressure,humidity,wind_direction]
            if any(field is None for field in required_fields):
                return JsonResponse({"error": "Missing required fields"}, status=400)
            

            reading_id, status= weather_model.insert_reading(
               device_name,
               precipitation,
               latitude,
               longitude,
               temperature,
               pressure,
               wind_speed,
               solar_radiation,
               vapor_pressure,
               humidity,
               wind_direction
              
            )
            return JsonResponse({"message": "Weather reading inserted", "id": reading_id}, status=status)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #get weather reading 
    if request.method == 'GET':
        try:
            login_username = request.GET.get('username')
            login_password = request.GET.get('password')
            reading_id = request.GET.get('id')

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing username or password"}, status=400)

            weather_model = WeatherReading()
            user_data, status = weather_model.login_check(login_username, login_password)

            if status != 200:
                return JsonResponse(user_data, status=status)

            weather_model.update_login(login_username)
            reading, status = weather_model.get_reading(reading_id)

            return JsonResponse(reading, safe=False, status=status)

        except Exception as e:
            return JsonResponse({"error": f"Error retrieving weather reading: {str(e)}"}, status=500)
        
    #update single reading data 
    if request.method == 'PUT':
        try:

            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get('username')
            login_password = data.get('password')

            reading_id = data.get('reading_id')
            update_data = data.get("update_data")

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing username or password"}, status=400)
            
            weather_model = WeatherReading()

            user_data, status = weather_model.login_check(login_username, login_password, required_role= 'Teacher')
            weather_model.update_login(login_username)

            if status != 200:
                return JsonResponse(user_data, status=status)

            # Validate the presence of reading_id
            if not reading_id:
                return JsonResponse({"error": "reading_id is required."}, status=400)

            
            result, status = weather_model.update_reading(reading_id, update_data)
            return JsonResponse(result, safe=False, status=status)
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error updating weather reading": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)
    
        
@csrf_exempt
def readings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            login_username = data.get('username')
            login_password = data.get('password')
            weathers = data.get('weathers')  # Expect a list of weather readings to be inserted

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing password or username"}, status=400)

            if not weathers or not isinstance(weathers, list):
                return JsonResponse({"error": "Invalid data format. Expect list of readings."}, status=400)
            
            weather_model = WeatherReading()
            weather_model.update_login(login_username)
            user_data, status = weather_model.login_check(login_username, login_password, required_role='Teacher')

            if status != 200:
                return JsonResponse(user_data, status=status)

            # Loop through the list and insert each weather reading
            for weather_list in weathers:
                device_name = weather_list.get('device_name')
                precipitation = weather_list.get('precipitation')
                latitude = weather_list.get('latitude')
                longitude = weather_list.get('longitude')
                temperature = weather_list.get('temperature')
                pressure = weather_list.get('pressure')
                wind_speed = weather_list.get('wind_speed')
                solar_radiation = weather_list.get('solar_radiation')
                vapor_pressure = weather_list.get('vapor_pressure')
                humidity = weather_list.get('humidity')
                wind_direction = weather_list.get('wind_direction')

                # Required fields check for each reading
                required_fields = [
                    device_name, precipitation, latitude, longitude, temperature,
                    pressure, wind_speed, solar_radiation, vapor_pressure, humidity, wind_direction
                ]
                
                if any(field is None for field in required_fields):
                    return JsonResponse({"error": f"Missing weather data for entry: {weather_list}"}, status=400)

            # Perform insertion into the database
            inserted_ids = weather_model.insert_multiple_reading(weathers)
            return JsonResponse({"message": "Weather readings inserted", "inserted_ids": inserted_ids}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
        
    if request.method == 'PATCH':
        try:
             data = json.loads(request.body.decode('utf-8'))
             login_username = data.get ('username')
             login_password = data.get ('password')
             updates = data.get('updates',[])

             if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)
            
             weather_model = WeatherReading()
             user_data, status = weather_model.login_check(login_username, login_password, required_role= 'Teacher')
             weather_model.update_login(login_username)

             if status != 200:
                return JsonResponse(user_data, status=status)
              # validate the structure of the update
             if not updates or not  isinstance(updates, list):
                 return JsonResponse({"Error": " invalid reading data expecting list of update"}, status=400)
             
             results, status = weather_model.update_readings(updates)
             return JsonResponse(results, safe=False, status=status)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error updating multiple weather reading": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)
    


    
    

         

#also maybe do not need this one as well 
@csrf_exempt
def get_readings(request):

    if request.method =='GET':
        try:
            login_username = request.GET.get('username')
            login_password = request.GET.get('password')
            query_parameter = request.GET.dict()#  convert query parameters to a dictionary for filtering 

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing username or password"}, status=400)


            weather_model = WeatherReading()
            user_data, status = weather_model.login_check(login_username, login_password)

            if status != 200:
                return JsonResponse(user_data, status=status)

            weather_model.update_login(login_username)
            
            
            readings = weather_model.get_readings(query_parameter)# implement filtering in get_readings()

            return JsonResponse(list(readings), safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error retireving weather reading": str(e)}, status=500)
    else:
         return JsonResponse({"error": "Invalid HTTP method"}, status=405)
        





#posibilly do not need this 

@csrf_exempt
def delete_reading(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get ('username')
            login_password = data.get ('password')
            reading_id = data.get('reading_id')

            if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)
            if not reading_id:
                 return JsonResponse({"error": "Missing reading id"}, status=400)

            
            weather_model = WeatherReading()
            user, status_code = weather_model.login_check(
                login_username, login_password, required_role='Teacher'
            )

            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)
            
            weather_model.update_login(login_username)

            result = weather_model.delete_reading(reading_id)

            if result:
                return JsonResponse({"message": "Weather reading deleted successfully"}, status=200)
            else:
                  return JsonResponse({"error": "Weather reading not found"}, status=404)
        
        except Exception as e:
            return JsonResponse({"error deleting weather reading": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# also this

@csrf_exempt
def delete_readings(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get ('username')
            login_password = data.get ('password')
            reading_ids = data.get('reading_ids',[])

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing passwrod or username"}, status=400)


            if not isinstance(reading_ids, list):
               return JsonResponse({"error": "Invalid reading_ids format"}, status=400)
            
            weather_model = WeatherReading()
            user, status_code = weather_model.login_check(
                login_username, login_password, required_role='Teacher'
            )
            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)
            
            weather_model.update_login(login_username)
            count_deleted = weather_model.delete_readings(reading_ids)

            return JsonResponse({"delete_count": count_deleted}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error deleting multiple weather reading": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)




            
