from rest_framework import serializers
from .models import Post, Reaction, Comment
from django.utils import timezone
from datetime import timedelta

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    time = serializers.SerializerMethodField()
    your_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'author', 'score', 'time', 'your_reaction', 'status', 'category', 'created_at', 'updated_at']

    def get_time(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        if diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() // 60)
            return f"{minutes} minutes ago" if minutes > 0 else "just now"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hours ago"
        else:
            days = diff.days
            return f"{days} days ago"

    def get_your_reaction(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            reaction = Reaction.objects.filter(user=user, post=obj).first()
            if reaction:
                return reaction.reaction 
        return None

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    self_comment = serializers.SerializerMethodField()
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'comment', 'created_at', 'updated_at', 'replies', 'self_comment']

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_self_comment(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.author == user
    
class PostDetailSerializer(PostSerializer):
    comments = serializers.SerializerMethodField()

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments']

    def get_comments(self, obj):
        comments = obj.comments.filter(comment__isnull=True)
        return CommentSerializer(comments, many=True, context=self.context).data