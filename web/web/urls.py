"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from test_app import views

urlpatterns = [
    path('', views.login, name='login'),
    path('login_judge/', views.login_judge, name='login_judge'),
    path('create_account/', views.create_account, name='create_account'),
    path('create_account_judge/', views.create_account_judge, name='create_account_judge'),
    path('system_interface/<int:account>/', views.system_interface, name='system_interface'),
    path('handle_data/', views.handle_data, name='handle_data'),
]
