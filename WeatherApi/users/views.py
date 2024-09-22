from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from .models import User
import logging

# Create your views here.
@csrf_exempt
def user(request):
    if request.method == 'POST':
        try:
            
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get ('login_username')
            login_password = data.get ('login_password')

            username = data.get('username')
            firstname = data.get('firstname')
            lastname = data.get('lastname')
            role = data.get('role')
            password = data.get('password', 'defaultpassword')

             
            if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)
             
            if not username or not role or not password or not firstname:
                return JsonResponse({"error": "missing required fields"}, status=400)
            
    
            user_model = User()
            user_model.update_login(login_username)
            
            user, status_code = user_model.login_check(
                login_username, login_password, required_role='Teacher'
            )

            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)

            #check if user is exist or not 
            if user_model.collection.find_one({"username": username}):
                return JsonResponse({"error": "User already exists"}, status=400) 
           
            user_id = user_model.insert_user(username, password, firstname, lastname, role)
            
            return JsonResponse({"message": "user created"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500) 


#delete user 
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get ('username')
            login_password = data.get ('password')
            user_id = data.get('user_id')

            if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)
            
            if not user_id:
                 return JsonResponse({"error": "Missing user id"}, status=400)

            user_model = User()
            user, status_code = user_model.login_check(
                login_username, login_password, required_role='Teacher'
            )

            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)
            
            user_model.update_login(login_username)

            result = user_model.delete_user(user_id)

            if result:
                return JsonResponse({"message": "user deleted successfully"}, status=200)
            else:
                  return JsonResponse({"error": "user not found"}, status=404)
        
        except Exception as e:
            return JsonResponse({"error deleting user": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)
    


@csrf_exempt
def users(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get ('username')
            login_password = data.get ('password')
            
            #extract filter from the request 
            role = data.get('role')
            last_login = data.get('last_login')

            filters = {}
            if role:
                filters['role'] = role
            if last_login:
                filters['last_login'] = last_login

            user_model = User()
            user, status_code = user_model.login_check(
                login_username, login_password, required_role='Teacher'
            )

            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)
            
            user_model.update_login(login_username)

            count_deleted, status = user_model.delete_users(filters)

            return JsonResponse({"count_delete": count_deleted}, status=status)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error deleting multiple user reading": str(e)}, status=500)
  

#update user by role 
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body.decode('utf-8'))
            login_username = data.get('username')
            login_password = data.get('password')

            date_range = data.get('date_range')  # Expects a dict with 'start_date' and 'end_date'
            new_role = data.get('new_role')

            if not login_username or not login_password:
                 return JsonResponse({"error": "Missing passwrod or username"}, status=400)

            # Validate input
            if  not date_range or not new_role:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # Initialize the model and call the update function
            user_model = User()
            user, status_code = user_model.login_check(
                login_username, login_password, required_role='Teacher'
            )

            if status_code != 200:  # Authentication failed
                return JsonResponse(user, status=status_code)
            
            user_model.update_login(login_username)
            response_data, status = user_model.update_user_role( date_range, new_role)

            return JsonResponse(response_data, status=status)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logging.error(f"Error processing update user access request: {e}")
            return JsonResponse({"error": "Server issue"}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)




