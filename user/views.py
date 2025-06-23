from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
# Create your views here.
class registerView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        User.objects.create_user(username=username, email=email, password=password)
    
        return Response({"message": "User created successfully"}, status=201)