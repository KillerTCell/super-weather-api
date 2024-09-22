from django.urls import path
from . import views

urlpatterns = [
      path('api/user/',views.user),
      path('api/users/',views.users)
    
]