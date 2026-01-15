# Tests for movies app
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Favorite, WatchLater, Library


class MovieModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.movie_data = {
            'id': 1,
            'title': 'Test Movie',
            'year': 2020,
            'desc': 'A test movie'
        }
    
    def test_create_favorite(self):
        favorite = Favorite.objects.create(
            user=self.user,
            movie_id=1,
            movie_data=self.movie_data
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.movie_id, 1)
    
    def test_create_watch_later(self):
        watch = WatchLater.objects.create(
            user=self.user,
            movie_id=1,
            movie_data=self.movie_data
        )
        self.assertEqual(watch.user, self.user)
    
    def test_create_library(self):
        lib = Library.objects.create(
            user=self.user,
            movie_id=1,
            movie_data=self.movie_data
        )
        self.assertEqual(lib.user, self.user)
