# myapp/urls.py
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('get_data_history_order/', views.get_data_history_order, name='get_data_history_order'),
]