from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('income', views.index, name='income'),
    path('add-income/', views.add_income, name='add-income'),
    path('edit-income/<int:id>/', views.edit_income, name='edit-income'),
    path('delete-income/<int:id>/', views.delete_income, name='delete-income'),
    path('search-income', csrf_exempt(views.search_income), name='search-income'),
]


