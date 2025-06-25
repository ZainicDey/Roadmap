from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from .serializers import PostSerializer, CommentSerializer, PostDetailSerializer

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

    existing_reaction = Reaction.objects.filter(user=user, post=post).first()

    if reaction_type == 'remove':
        if existing_reaction:
            if existing_reaction.reaction == 'like':
                post.score -= 1
            else:
                post.score += 1
            existing_reaction.delete()
            post.save()
    else:
        if existing_reaction:
            if existing_reaction.reaction == reaction_type:
                return Response({'detail': f'Already {reaction_type}d.'}, status=200)
            else:
                if reaction_type == 'dislike':
                    post.score -= 2
                else:
                    post.score += 2
                existing_reaction.reaction = reaction_type
                existing_reaction.save()
                post.save()
        else:
            Reaction.objects.create(user=user, post=post, reaction=reaction_type)
            post.score += 1 if reaction_type == 'like' else -1
            post.save()

    return Response({
        'score': post.score,
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
    
from django.db.models import F, ExpressionWrapper, IntegerField

class PostViewSet(ModelViewSet):
    def get_queryset(self):
        return Post.objects.all()
    
    ordering_fields = ['created_at', 'updated_at', 'score']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        else:
            return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        ordering = request.query_params.get('ordering')
        category = request.query_params.get('category')
        status = request.query_params.get('status')
        print(f"Ordering: {ordering}, Category: {category}, Status: {status}")
        if category:
            queryset = queryset.filter(category__iexact=category)
        if status:
            queryset = queryset.filter(status__iexact=status)
        if ordering == 'score':
            queryset = queryset.order_by('-score')
        elif ordering == '-created_at':
            queryset = queryset.order_by('-created_at')
        elif ordering == 'created_at':
            queryset = queryset.order_by('created_at')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        if post_id:
            return self.queryset.filter(post_id=post_id)
        return self.queryset

    def create(self, request):
        post_id = request.data.get('post_id')
        content = request.data.get('content')
        comment_id = request.data.get('comment_id')

        if not post_id or not content:
            return Response({'detail': 'Post ID and content are required.'}, status=400)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=404)

        parent_comment = None
        if comment_id:
            try:
                parent_comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({'detail': 'Parent comment not found.'}, status=404)

        try:
            comment = Comment(
                post=post,
                author=request.user,
                content=content,
                comment=parent_comment
            )
            comment.save()
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)