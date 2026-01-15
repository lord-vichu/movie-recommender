import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Favorite, WatchLater, Library, UserRating
import json
import urllib.parse


def get_wikipedia_summary(search_term):
    """Fetch Wikipedia summary for a search term"""
    try:
        # Wikipedia API endpoint
        wiki_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        encoded_term = urllib.parse.quote(search_term)
        
        response = requests.get(
            f"{wiki_url}{encoded_term}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'thumbnail': data.get('thumbnail', {}).get('source') if data.get('thumbnail') else None,
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'description': data.get('description', '')
            }
    except Exception as e:
        print(f"Wikipedia API error: {e}")
    
    return None


def index(request):
    """Main page view"""
    return render(request, 'movies/index.html')


@require_http_methods(["POST"])
def user_signup(request):
    """User registration"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)
        
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return JsonResponse({'success': True, 'username': username})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def user_signin(request):
    """User login"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        user = authenticate(username=username, password=password)
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        login(request, user)
        return JsonResponse({'success': True, 'username': username})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def user_signout(request):
    """User logout"""
    logout(request)
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET"])
def get_favorites(request):
    """Get user's favorite movies"""
    favorites = Favorite.objects.filter(user=request.user)
    data = [fav.movie_data for fav in favorites]
    return JsonResponse({'favorites': data})


@login_required
@require_http_methods(["POST"])
def add_favorite(request):
    """Add movie to favorites"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        movie_data = data.get('movie_data', {})
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={'movie_data': movie_data}
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'message': 'Added to favorites' if created else 'Already in favorites'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_favorite(request):
    """Remove movie from favorites"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()
        
        return JsonResponse({
            'success': True,
            'deleted': deleted_count > 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_watch_later(request):
    """Get user's watch later list"""
    watch_later = WatchLater.objects.filter(user=request.user)
    data = [item.movie_data for item in watch_later]
    return JsonResponse({'watch_later': data})


@login_required
@require_http_methods(["POST"])
def add_watch_later(request):
    """Add movie to watch later"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        movie_data = data.get('movie_data', {})
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        item, created = WatchLater.objects.get_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={'movie_data': movie_data}
        )
        
        return JsonResponse({
            'success': True,
            'created': created
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_watch_later(request):
    """Remove movie from watch later"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        deleted_count, _ = WatchLater.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()
        
        return JsonResponse({
            'success': True,
            'deleted': deleted_count > 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_library(request):
    """Get user's library"""
    library = Library.objects.filter(user=request.user)
    data = [item.movie_data for item in library]
    return JsonResponse({'library': data})


@login_required
@require_http_methods(["POST"])
def add_library(request):
    """Add movie to library"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        movie_data = data.get('movie_data', {})
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        item, created = Library.objects.get_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={'movie_data': movie_data}
        )
        
        return JsonResponse({
            'success': True,
            'created': created
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_library(request):
    """Remove movie from library"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return JsonResponse({'error': 'Movie ID required'}, status=400)
        
        deleted_count, _ = Library.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()
        
        return JsonResponse({
            'success': True,
            'deleted': deleted_count > 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def discover_movies(request):
    """Discover movies from TMDb API with filters"""
    try:
        genre = request.GET.get('genre', 'Any')
        language = request.GET.get('language', 'Any')
        timeframe = request.GET.get('timeframe', 'any')
        count = int(request.GET.get('count', 20))
        
        # Genre mapping
        genre_map = {
            'Action': 28, 'Comedy': 35, 'Drama': 18, 'Horror': 27,
            'Romance': 10749, 'Thriller': 53, 'Sci-Fi': 878, 'Crime': 80,
            'Animation': 16, 'Fantasy': 14, 'Biopic': 18
        }
        
        # Language mapping
        language_map = {
            'English': 'en', 'Hindi': 'hi', 'Malayalam': 'ml',
            'Tamil': 'ta', 'Korean': 'ko'
        }
        
        # Build API URL
        params = {
            'api_key': settings.TMDB_API_KEY,
            'sort_by': 'popularity.desc',
            'vote_count.gte': 100
        }
        
        if genre != 'Any' and genre in genre_map:
            params['with_genres'] = genre_map[genre]
        
        if language != 'Any' and language in language_map:
            params['with_original_language'] = language_map[language]
        
        # Timeframe filter
        from datetime import datetime
        current_year = datetime.now().year
        
        if timeframe == 'old':
            params['primary_release_date.lte'] = '2009-12-31'
        elif timeframe == 'new':
            params['primary_release_date.gte'] = '2011-01-01'
            params['primary_release_date.lte'] = f'{current_year}-12-31'
        else:
            params['primary_release_date.lte'] = f'{current_year}-12-31'
        
        # Fetch multiple pages
        pages = min(15, max(1, count // 20))
        all_movies = []
        
        for page in range(1, pages + 1):
            params['page'] = page
            response = requests.get(
                f'{settings.TMDB_BASE_URL}/discover/movie',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                all_movies.extend(data.get('results', []))
        
        # Format movies
        movies = []
        for movie in all_movies[:count]:
            movies.append({
                'id': movie.get('id'),
                'title': movie.get('title') or movie.get('original_title'),
                'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
                'genres': movie.get('genre_ids', []),
                'lang': movie.get('original_language'),
                'desc': movie.get('overview', 'No description available.'),
                'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
                'rating': round(movie.get('vote_average', 0), 1) if movie.get('vote_average') else None,
                'backdrop': f"{settings.TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None
            })
        
        return JsonResponse({'movies': movies})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_trending(request):
    """Get trending movies"""
    try:
        response = requests.get(
            f'{settings.TMDB_BASE_URL}/trending/movie/day',
            params={'api_key': settings.TMDB_API_KEY},
            timeout=10
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch trending movies'}, status=500)
        
        data = response.json()
        movies = []
        
        for movie in data.get('results', [])[:20]:
            movies.append({
                'id': movie.get('id'),
                'title': movie.get('title') or movie.get('original_title'),
                'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
                'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
                'rating': round(movie.get('vote_average', 0), 1) if movie.get('vote_average') else None
            })
        
        return JsonResponse({'trending': movies})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_movie_details(request, movie_id):
    """Get detailed movie information"""
    try:
        response = requests.get(
            f'{settings.TMDB_BASE_URL}/movie/{movie_id}',
            params={
                'api_key': settings.TMDB_API_KEY,
                'append_to_response': 'credits,videos,images,similar,release_dates'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Movie not found'}, status=404)
        
        movie = response.json()
        
        # Format response
        data = {
            'id': movie.get('id'),
            'title': movie.get('title'),
            'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
            'desc': movie.get('overview'),
            'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
            'backdrop': f"{settings.TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None,
            'rating': round(movie.get('vote_average', 0), 1),
            'genres': [g['name'] for g in movie.get('genres', [])],
            'runtime': movie.get('runtime'),
            'budget': movie.get('budget'),
            'revenue': movie.get('revenue'),
            'tagline': movie.get('tagline'),
            'status': movie.get('status'),
            'lang': movie.get('original_language'),
            'cast': [],
            'crew': [],
            'videos': [],
            'images': [],
            'similar': [],
            'wikipedia': None
        }
        
        # Try to get Wikipedia info
        movie_title = movie.get('title')
        if movie_title:
            # Try with year first for better accuracy
            wiki_search = f"{movie_title} ({data['year']} film)" if data['year'] else f"{movie_title} film"
            wiki_data = get_wikipedia_summary(wiki_search)
            if not wiki_data or not wiki_data.get('extract'):
                # Fallback to just movie title
                wiki_data = get_wikipedia_summary(movie_title)
            data['wikipedia'] = wiki_data
        
        # Cast
        credits = movie.get('credits', {})
        if 'cast' in credits:
            data['cast'] = [{
                'id': person.get('id'),
                'name': person.get('name'),
                'character': person.get('character'),
                'profile': f"{settings.TMDB_IMAGE_BASE}{person.get('profile_path')}" if person.get('profile_path') else None
            } for person in credits['cast'][:10]]
        
        # Crew
        if 'crew' in credits:
            data['crew'] = [{
                'id': person.get('id'),
                'name': person.get('name'),
                'job': person.get('job'),
                'department': person.get('department')
            } for person in credits['crew'] if person.get('job') in ['Director', 'Writer', 'Screenplay', 'Producer']]
        
        # Videos
        videos = movie.get('videos', {}).get('results', [])
        data['videos'] = [{
            'key': v.get('key'),
            'name': v.get('name'),
            'type': v.get('type'),
            'site': v.get('site')
        } for v in videos if v.get('site') == 'YouTube']
        
        # Similar movies
        similar = movie.get('similar', {}).get('results', [])
        data['similar'] = [{
            'id': m.get('id'),
            'title': m.get('title'),
            'year': int(m.get('release_date', '0000')[:4]) if m.get('release_date') else None,
            'poster': f"{settings.TMDB_IMAGE_BASE}{m.get('poster_path')}" if m.get('poster_path') else None
        } for m in similar[:10]]
        
        return JsonResponse({'movie': data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_person_details(request, person_id):
    """Get person (actor/director) details"""
    try:
        response = requests.get(
            f'{settings.TMDB_BASE_URL}/person/{person_id}',
            params={
                'api_key': settings.TMDB_API_KEY,
                'append_to_response': 'movie_credits'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Person not found'}, status=404)
        
        person = response.json()
        
        data = {
            'id': person.get('id'),
            'name': person.get('name'),
            'biography': person.get('biography'),
            'birthday': person.get('birthday'),
            'place_of_birth': person.get('place_of_birth'),
            'profile_path': f"{settings.TMDB_IMAGE_BASE}{person.get('profile_path')}" if person.get('profile_path') else None,
            'known_for': [],
            'wikipedia': None
        }
        
        # Try to get Wikipedia info
        person_name = person.get('name')
        if person_name:
            wiki_data = get_wikipedia_summary(person_name)
            data['wikipedia'] = wiki_data
        
        # Known for
        credits = person.get('movie_credits', {}).get('cast', [])
        sorted_credits = sorted(credits, key=lambda x: x.get('popularity', 0), reverse=True)
        data['known_for'] = [{
            'id': m.get('id'),
            'title': m.get('title'),
            'year': int(m.get('release_date', '0000')[:4]) if m.get('release_date') else None,
            'poster': f"{settings.TMDB_IMAGE_BASE}{m.get('poster_path')}" if m.get('poster_path') else None
        } for m in sorted_credits[:8]]
        
        return JsonResponse({'person': data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
