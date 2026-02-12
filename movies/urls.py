from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Landing page
    path('landing/', views.landing, name='landing'),
    
    # Main page
    path('', views.index, name='index'),
    
    # Authentication
    path('api/auth/signup/', views.user_signup, name='signup'),
    path('api/auth/signin/', views.user_signin, name='signin'),
    path('api/auth/signout/', views.user_signout, name='signout'),
    
    # Favorites
    path('api/favorites/', views.get_favorites, name='get_favorites'),
    path('api/favorites/add/', views.add_favorite, name='add_favorite'),
    path('api/favorites/remove/', views.remove_favorite, name='remove_favorite'),
    
    # Watch Later
    path('api/watch-later/', views.get_watch_later, name='get_watch_later'),
    path('api/watch-later/add/', views.add_watch_later, name='add_watch_later'),
    path('api/watch-later/remove/', views.remove_watch_later, name='remove_watch_later'),
    
    # Library
    path('api/library/', views.get_library, name='get_library'),
    path('api/library/add/', views.add_library, name='add_library'),
    path('api/library/remove/', views.remove_library, name='remove_library'),
    
    # Movies
    path('api/movies/discover/', views.discover_movies, name='discover_movies'),
    path('api/movies/trending/', views.get_trending, name='get_trending'),
    path('api/movies/<int:movie_id>/', views.get_movie_details, name='get_movie_details'),
    
    # Person details
    path('api/person/<int:person_id>/', views.get_person_details, name='get_person_details'),
]
