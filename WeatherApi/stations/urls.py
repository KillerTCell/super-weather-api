from django.urls import path
from . import views

urlpatterns = [
  path('api/station/', views.station),
  path('api/stations/', views.stations)

]