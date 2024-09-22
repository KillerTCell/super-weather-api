from django.shortcuts import render
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WeatherReading
import logging


# Create your views here.
@csrf_exempt
def analyses(request):
    if request.method == 'GET':
        try:
            login_username = request.GET.get('username')
            login_password = request.GET.get('password')
            query_parameter = request.GET.dict()

            if not login_username or not login_password:
                return JsonResponse({"error": "Missing username or password"}, status=400)

            weather_model = WeatherReading()

            # Check user credentials
            user_data, status = weather_model.login_check(login_username, login_password)
            weather_model.update_login(login_username)

            if status != 200:
                return JsonResponse(user_data, status=status)

            # Determine which analysis to perform based on provided parameters
            if  query_parameter.get('Date_range'):
                try:
                # Get max temperature
                    max_temp_data, status = weather_model.find_max_temperature(query_parameter)
                    return JsonResponse(max_temp_data, status=status)
                except Exception as e:
                    logging.error(f"Missing date range: {e}")
                    return JsonResponse({"error": str(e)}, status=400)


            elif query_parameter.get('Device Name') and query_parameter.get('Time'):
                try:
                # Get weather by station
                    weather_data, status = weather_model.find_weather_by_station(query_parameter)
                    return JsonResponse(weather_data, status=status)
                except Exception as e:
                    logging.error(f"Missing device name or time: {e}")
                    return JsonResponse({"error": str(e)}, status=400)


            elif query_parameter.get('Device Name') and query_parameter.get('Time'):
                try:
                    # Get max precipitation
                    max_precipitation, status = weather_model.find_max_precipitation(query_parameter)
                    return JsonResponse(max_precipitation, status=status)
                except Exception as e:
                    logging.error(f"Missing device name or time: {e}")
                    return JsonResponse({"error": str(e)}, status=400)


            # If none of the expected parameters are provided
            else:
                return JsonResponse({"error": "Missing required parameters for analysis"}, status=400)

        except Exception as e:
            logging.error(f"Error processing analysis request: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)



        
        