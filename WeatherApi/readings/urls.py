from django.urls import path
from . import views

urlpatterns = [
    path('api/reading/', views.reading),
    path('api/readings/', views.readings)
  
]