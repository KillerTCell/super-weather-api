from django.shortcuts import render
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Station
import logging


# Create your views here.
from django.http import JsonResponse
import json
import logging


@csrf_exempt
def station(request):
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
            
            station_model = Station()
            station_model.update_login(login_username)
            user_data, status = station_model.login_check(login_username, login_password, required_role='Sensor')
            

            if status != 200:
                return JsonResponse(user_data, status=status)
            
            
            required_fields = [device_name, precipitation,latitude,longitude,temperature,pressure,wind_speed,solar_radiation,vapor_pressure,humidity,wind_direction]
            if any(field is None for field in required_fields):
                return JsonResponse({"error": "Missing required fields"}, status=400)
            

            reading_id, status= station_model.insert_reading(
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
    else:
         return JsonResponse({"error": "Invalid HTTP method"}, status=405)
        
@csrf_exempt
def stations(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            login_username = data.get('username')
            login_password = data.get('password')
            weathers = data.get('weathers')# expect a list of weather reading to be insert

            if not login_username or not login_password:
              return JsonResponse({"error": "Missing passwrod or username"}, status=400)

            
            if not weathers or not isinstance(weathers, list):
                return JsonResponse({"error": "Invalid data format. Expect list of reading."}, status=400)
            
            station_model = Station()
            station_model.update_login(login_username)
            user_data, status = station_model.login_check(login_username, login_password, required_role='Teacher')
            

            if status != 200:
                return JsonResponse(user_data, status=status)
           
             

            # loop to the list and insert each wether reading 
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
                

                required_fields = [device_name,precipitation,latitude,longitude,temperature,pressure,wind_speed,solar_radiation,vapor_pressure,humidity,wind_direction]
            if any(field is None for field in required_fields):
                return JsonResponse({"error": "Missing weather data"}, status=400)
            #need some check so the same weather data is not inserted into the database

            inserted_ids = station_model.insert_multiple_reading(weathers)
            return JsonResponse({"message": "Weather reading inserted", "inserted_ids": inserted_ids}, status=status)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    

    
    if request.method =='GET':
        try:
            login_username = request.GET.get('username')
            login_password = request.GET.get('password')
            query_parameter = request.GET.dict()#  convert query parameters to a dictionary for filtering 

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing username or password"}, status=400)


            station_model = Station()
            user_data, status = station_model.login_check(login_username, login_password)

            if status != 200:
                return JsonResponse(user_data, status=status)

            station_model.update_login(login_username)

           
            readings, status = station_model.get_readings(query_parameter)# implement filtering in get_readings()

            if status != 200:
                return JsonResponse(readings, status=status)

            return JsonResponse(list(readings), safe=False, status=status)
        except Exception as e:
            return JsonResponse({"error retireving weather reading": str(e)}, status=500)
    else:
         return JsonResponse({"error": "Invalid HTTP method"}, status=405)
    