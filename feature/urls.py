from django.urls import path,include
from .views import react_to_post
from .views import PostViewSet, CommentViewSet, register_views

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='post-comments')
urlpatterns = [
    path('posts/<int:post_id>/react/', react_to_post),
    path('', include(router.urls)),
    path('register/', register_views),
]