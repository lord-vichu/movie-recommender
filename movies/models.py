from django.db import models
from django.contrib.auth.models import User


class MovieCache(models.Model):
    """Cache for storing movie data from TMDb API"""
    movie_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    genres = models.JSONField(default=list)
    language = models.CharField(max_length=50)
    description = models.TextField()
    poster_url = models.URLField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    backdrop_url = models.URLField(null=True, blank=True)
    cached_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-cached_at']
    
    def __str__(self):
        return f"{self.title} ({self.year})"


class IMDbMovie(models.Model):
    """Local catalog built from free IMDb datasets"""
    tconst = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    year = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=16, default='unknown')
    countries = models.CharField(max_length=128, blank=True)
    genres = models.JSONField(default=list)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    votes = models.IntegerField(default=0)
    plot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-votes', '-rating', 'title']

    def __str__(self):
        return f"{self.title} ({self.year})"


class Favorite(models.Model):
    """User's favorite movies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    movie_id = models.IntegerField()
    movie_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie_data.get('title', 'Unknown')}"


class WatchLater(models.Model):
    """Movies user wants to watch later"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_later')
    movie_id = models.IntegerField()
    movie_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie_data.get('title', 'Unknown')}"


class Library(models.Model):
    """User's movie library"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library')
    movie_id = models.IntegerField()
    movie_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie_data.get('title', 'Unknown')}"


class UserRating(models.Model):
    """User ratings for movies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie_id = models.IntegerField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'movie_id')
    
    def __str__(self):
        return f"{self.user.username} - Movie {self.movie_id} - {self.rating}/10"
