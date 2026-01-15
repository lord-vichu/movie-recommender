from django.contrib import admin
from .models import MovieCache, Favorite, WatchLater, Library, UserRating


@admin.register(MovieCache)
class MovieCacheAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'language', 'rating', 'cached_at')
    list_filter = ('language', 'year')
    search_fields = ('title',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie_id', 'created_at')
    list_filter = ('user', 'created_at')


@admin.register(WatchLater)
class WatchLaterAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie_id', 'created_at')
    list_filter = ('user', 'created_at')


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie_id', 'created_at')
    list_filter = ('user', 'created_at')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie_id', 'rating', 'created_at')
    list_filter = ('user', 'rating', 'created_at')
