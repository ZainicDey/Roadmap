from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from .serializers import PostSerializer, CommentSerializer, PostDetailSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Post, Reaction, Comment

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def react_to_post(request, post_id):
    user = request.user
    reaction_type = request.data.get('reaction')

    if reaction_type not in ['like', 'dislike', 'remove']:
        return Response({'detail': 'Invalid reaction type.'}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=404)

    if not Reaction.objects.filter(user=user, post=post).exists():
        existing_reaction = None

    if reaction_type == 'remove':
        if existing_reaction:
            if existing_reaction.reaction == 'like':
                post.like_count -= 1
            else:
                post.dislike_count -= 1
            existing_reaction.delete()
            post.save()
    else:
        if existing_reaction:
            if existing_reaction.reaction == reaction_type:
                return Response({'detail': f'Already {reaction_type}d.'}, status=200)
            else:
                if existing_reaction.reaction == 'like':
                    post.like_count -= 1
                    post.dislike_count += 1
                else:
                    post.dislike_count -= 1
                    post.like_count += 1
                existing_reaction.reaction = reaction_type
                existing_reaction.save()
                post.save()
        else:
            # New reaction
            Reaction.objects.create(user=user, post=post, reaction=reaction_type)
            if reaction_type == 'like':
                post.like_count += 1
            else:
                post.dislike_count += 1
            post.save()

    return Response({
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
        'your_reaction': reaction_type if reaction_type != 'remove' else None
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comment_on_post(request, post_id):
    user = request.user
    content = request.data.get('content')

    if not content:
        return Response({'detail': 'Content cannot be empty.'}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=404)

    comment = Comment.objects.create(post=post, author=user, content=content)
    serializer = CommentSerializer(comment, context={'request': request})

    return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        else:
            return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer