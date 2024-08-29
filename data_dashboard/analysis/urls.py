from django.urls import path
from . import views  # Import the views from the current package

urlpatterns = [
    # The home page (file upload page)
    path('', views.upload_file, name='upload_file'),
]
