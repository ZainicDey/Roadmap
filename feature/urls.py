from django.urls import path,include
from .views import react_to_post
from .views import PostViewSet

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('posts/<int:post_id>/react/', react_to_post),
    path('', include(router.urls)),
]