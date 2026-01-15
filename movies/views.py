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

try:
    from Levenshtein import ratio as levenshtein_ratio
except ImportError:
    # Fallback to simple string matching if Levenshtein not available
    def levenshtein_ratio(a, b):
        a, b = a.lower(), b.lower()
        if a == b:
            return 1.0
        if a in b or b in a:
            return 0.8
        return 0.0


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


def search_wikipedia_movies(query, count=10):
    """Search Wikipedia for movies and return formatted results with multiple strategies"""
    try:
        movies = []
        seen_titles = set()
        
        search_url = "https://en.wikipedia.org/w/api.php"
        
        # Strategy 1: Direct search with multiple variations
        search_queries = [
            f"{query} films",
            f"{query} cinema",
            f"List of {query} films",
            f"{query} film industry",
            f"{query} movies",
            query,
            f"{query}-language films",
            f"{query} language cinema",
        ]
        
        for search_term in search_queries:
            if len(movies) >= count:
                break
                
            try:
                search_params = {
                    'action': 'opensearch',
                    'search': search_term,
                    'limit': 50,  # Get many more results
                    'namespace': 0,
                    'format': 'json'
                }
                
                response = requests.get(search_url, params=search_params, timeout=10)
                if response.status_code != 200:
                    continue
                
                search_results = response.json()
                titles = search_results[1] if len(search_results) > 1 else []
                
                for title in titles:
                    if len(movies) >= count:
                        break
                        
                    if title.lower() in seen_titles:
                        continue
                    
                    # More lenient filtering - accept any article that might be movie-related
                    title_lower = title.lower()
                    
                    # Accept if contains movie keywords OR is in a list
                    is_movie_related = (
                        any(keyword in title_lower for keyword in ['film', 'movie', 'cinema']) or
                        'list of' in title_lower
                    )
                    
                    if is_movie_related:
                        seen_titles.add(title.lower())
                        
                        try:
                            wiki_data = get_wikipedia_summary(title)
                            if wiki_data and wiki_data.get('extract'):
                                import re
                                year_match = re.search(r'\((\d{4})', title)
                                year = int(year_match.group(1)) if year_match else None
                                
                                clean_title = wiki_data.get('title', title)
                                clean_title = re.sub(r'\s*\(.*?\)\s*', '', clean_title)
                                clean_title = clean_title.replace(' film', '').replace(' movie', '').strip()
                                
                                movies.append({
                                    'id': f"wiki_{title.replace(' ', '_')}",
                                    'title': clean_title,
                                    'year': year,
                                    'genres': [],
                                    'lang': 'en',
                                    'desc': wiki_data.get('extract', 'No description available.'),
                                    'poster': wiki_data.get('thumbnail'),
                                    'rating': None,
                                    'backdrop': wiki_data.get('thumbnail'),
                                    'source': 'wikipedia',
                                    'wiki_url': wiki_data.get('url', '')
                                })
                        except Exception as detail_err:
                            print(f"Error getting details for '{title}': {detail_err}")
                            continue
                            
            except Exception as search_err:
                print(f"Wikipedia search error for '{search_term}': {search_err}")
                continue
        
        # Strategy 2: Category-based search with multiple category names
        if len(movies) < count:
            category_variations = [
                f"{query} films",
                f"{query} cinema",
                f"{query}-language films",
                f"{query} film",
            ]
            
            for cat_name in category_variations:
                if len(movies) >= count:
                    break
                    
                try:
                    category_params = {
                        'action': 'query',
                        'list': 'categorymembers',
                        'cmtitle': f'Category:{cat_name}',
                        'cmlimit': 100,  # Get many results
                        'format': 'json'
                    }
                    
                    cat_response = requests.get(search_url, params=category_params, timeout=10)
                    if cat_response.status_code == 200:
                        cat_data = cat_response.json()
                        members = cat_data.get('query', {}).get('categorymembers', [])
                        
                        for member in members:
                            if len(movies) >= count:
                                break
                            
                            member_title = member.get('title', '')
                            if member_title.lower() in seen_titles:
                                continue
                            
                            seen_titles.add(member_title.lower())
                            
                            try:
                                wiki_data = get_wikipedia_summary(member_title)
                                
                                if wiki_data and wiki_data.get('extract'):
                                    import re
                                    year_match = re.search(r'\((\d{4})', member_title)
                                    year = int(year_match.group(1)) if year_match else None
                                    
                                    clean_title = wiki_data.get('title', member_title)
                                    clean_title = re.sub(r'\s*\(.*?\)\s*', '', clean_title)
                                    clean_title = clean_title.replace(' film', '').replace(' movie', '').strip()
                                    
                                    movies.append({
                                        'id': f"wiki_{member_title.replace(' ', '_')}",
                                        'title': clean_title,
                                        'year': year,
                                        'genres': [],
                                        'lang': 'en',
                                        'desc': wiki_data.get('extract', 'No description available.'),
                                        'poster': wiki_data.get('thumbnail'),
                                        'rating': None,
                                        'backdrop': wiki_data.get('thumbnail'),
                                        'source': 'wikipedia',
                                        'wiki_url': wiki_data.get('url', '')
                                    })
                            except Exception as detail_err:
                                print(f"Error getting category member details: {detail_err}")
                                continue
                                
                except Exception as cat_err:
                    print(f"Wikipedia category search error for '{cat_name}': {cat_err}")
                    continue
        
        print(f"Wikipedia search for '{query}' returned {len(movies)} movies")
        return movies[:count]
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []
        
        return movies[:count]
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []


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
    """Discover movies from TMDb API with filters, fallback to Wikipedia"""
    try:
        genre = request.GET.get('genre', 'Any')
        language = request.GET.get('language', 'Any')
        timeframe = request.GET.get('timeframe', 'any')
        count = int(request.GET.get('count', 20))
        search_query = request.GET.get('search', '').strip()  # Add search parameter
        
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
        
        movies = []
        
        # If there's a specific search query, use aggressive fuzzy matching
        if search_query:
            tmdb_results = []
            search_terms = [search_query]
            
            # Generate search variations for better matching
            query_lower = search_query.lower()
            
            # Word-by-word search for multi-word queries
            if ' ' in search_query:
                words = search_query.split()
                # Try each word individually
                search_terms.extend(words)
                # Try combinations
                if len(words) >= 2:
                    search_terms.append(' '.join(words[:2]))  # First two words
                    search_terms.append(' '.join(words[-2:]))  # Last two words
            
            # Common spelling variations
            variations = [
                query_lower.replace('tion', 'sion'),
                query_lower.replace('sion', 'tion'),
                query_lower.replace('er', 'or'),
                query_lower.replace('or', 'er'),
                query_lower.replace('ie', 'y'),
                query_lower.replace('y', 'ie'),
                query_lower.replace('ph', 'f'),
                query_lower.replace('f', 'ph'),
                query_lower.replace('c', 'k'),
                query_lower.replace('k', 'c'),
            ]
            search_terms.extend([v for v in variations if v != query_lower])
            
            # Remove duplicates
            search_terms = list(dict.fromkeys(search_terms))
            
            # Search TMDb with all variations (limit to first 10 terms to avoid too many requests)
            seen_ids = set()
            for term in search_terms[:10]:
                try:
                    # Search multiple pages for each term
                    for page in range(1, 3):  # Search 2 pages per term
                        search_response = requests.get(
                            f'{settings.TMDB_BASE_URL}/search/movie',
                            params={
                                'api_key': settings.TMDB_API_KEY,
                                'query': term,
                                'page': page
                            },
                            timeout=10
                        )
                        
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                            results = search_data.get('results', [])
                            
                            for movie in results:
                                movie_id = movie.get('id')
                                if movie_id not in seen_ids:
                                    seen_ids.add(movie_id)
                                    tmdb_results.append(movie)
                            
                            # If we found good results, no need to search more pages
                            if len(results) > 15:
                                break
                except Exception as e:
                    print(f"Search error for term '{term}': {e}")
                    continue
                
                # Stop if we have enough results
                if len(tmdb_results) > 50:
                    break
            
            # Score ALL results by similarity (more lenient threshold)
            scored_results = []
            for movie in tmdb_results:
                title = (movie.get('title', '') or movie.get('original_title', '')).lower()
                original_title = (movie.get('original_title', '') or '').lower()
                
                # Check similarity with both title and original title
                similarity_title = levenshtein_ratio(query_lower, title)
                similarity_original = levenshtein_ratio(query_lower, original_title)
                max_similarity = max(similarity_title, similarity_original)
                
                # Also check partial matches
                if query_lower in title or title in query_lower:
                    max_similarity = max(max_similarity, 0.85)
                if query_lower in original_title or original_title in query_lower:
                    max_similarity = max(max_similarity, 0.85)
                
                # Include if similarity is above 0.3 (very lenient)
                if max_similarity > 0.3:
                    scored_results.append((max_similarity, movie))
            
            # Sort by similarity score (highest first)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Format TMDb results
            for similarity, movie in scored_results[:count]:
                movies.append({
                    'id': movie.get('id'),
                    'title': movie.get('title') or movie.get('original_title'),
                    'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
                    'genres': movie.get('genre_ids', []),
                    'lang': movie.get('original_language'),
                    'desc': movie.get('overview', 'No description available.'),
                    'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
                    'rating': round(movie.get('vote_average', 0), 1) if movie.get('vote_average') else None,
                    'backdrop': f"{settings.TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None,
                    'source': 'tmdb',
                    'match_score': round(similarity * 100, 1)  # Add match score for debugging
                })
            
            # Always add Wikipedia results for broader coverage
            if len(movies) < count:
                wiki_movies = search_wikipedia_movies(search_query, count - len(movies))
                movies.extend(wiki_movies)
        else:
            # Regular discover mode (no specific search query)
            # Build API URL
            params = {
                'api_key': settings.TMDB_API_KEY,
                'sort_by': 'popularity.desc',
                'vote_count.gte': 100
            }
            
            selected_genre_name = None
            if genre != 'Any' and genre in genre_map:
                params['with_genres'] = genre_map[genre]
                selected_genre_name = genre
            
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
                    'backdrop': f"{settings.TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None,
                    'source': 'tmdb'
                })
            
            # Always try to supplement with Wikipedia if we don't have enough movies
            remaining_count = count - len(movies)
            print(f"TMDb returned {len(movies)} movies, need {remaining_count} more")
            
            # ALWAYS search Wikipedia for language-specific queries to ensure we get 20 movies
            if language != 'Any':
                # Create language-specific search queries for Wikipedia
                language_names = {
                    'English': 'english', 'Hindi': 'hindi', 'Malayalam': 'malayalam',
                    'Tamil': 'tamil', 'Korean': 'korean'
                }
                if language in language_names:
                    lang_name = language_names[language]
                    # Calculate how many we need (always try to get full count from Wikipedia)
                    wiki_count_needed = max(count - len(movies), count // 2)  # Get at least half from Wikipedia
                    print(f"Searching Wikipedia for {wiki_count_needed} {lang_name} movies")
                    
                    # Try multiple search terms
                    search_terms = [
                        lang_name,
                        f"{lang_name} cinema",
                        f"{lang_name}-language",
                    ]
                    
                    for search_term in search_terms:
                        if len(movies) >= count:
                            break
                        wiki_movies = search_wikipedia_movies(search_term, count - len(movies))
                        print(f"Wikipedia search '{search_term}' returned {len(wiki_movies)} movies")
                        movies.extend(wiki_movies)
                    
                    print(f"After Wikipedia: Total {len(movies)} movies")
            
            # If genre was selected and we still need more, search Wikipedia
            elif remaining_count > 0 and selected_genre_name and selected_genre_name != 'Any':
                wiki_query = f"{selected_genre_name.lower()}"
                print(f"Searching Wikipedia for {remaining_count} {wiki_query} movies")
                wiki_movies = search_wikipedia_movies(wiki_query, remaining_count)
                movies.extend(wiki_movies)
        
        print(f\"Final movie count: {len(movies)}\")
        return JsonResponse({'movies': movies[:count]})  # Limit to requested count
    
    except Exception as e:
        print(f\"Error in discover_movies: {e}\")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_trending(request):
    """Get trending movies from TMDb and popular movies from Wikipedia"""
    try:
        movies = []
        
        # Get TMDb trending movies
        response = requests.get(
            f'{settings.TMDB_BASE_URL}/trending/movie/day',
            params={'api_key': settings.TMDB_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            for movie in data.get('results', [])[:15]:
                movies.append({
                    'id': movie.get('id'),
                    'title': movie.get('title') or movie.get('original_title'),
                    'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
                    'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
                    'rating': round(movie.get('vote_average', 0), 1) if movie.get('vote_average') else None,
                    'source': 'tmdb'
                })
        
        # Add some popular Wikipedia movies to supplement
        try:
            wiki_search_terms = ['2024 films', '2025 films', 'blockbuster films']
            for term in wiki_search_terms:
                wiki_movies = search_wikipedia_movies(term, 5)
                movies.extend(wiki_movies[:2])  # Add 2 from each search
                if len(movies) >= 20:
                    break
        except Exception as wiki_err:
            print(f"Wikipedia trending fetch error: {wiki_err}")
        
        return JsonResponse({'trending': movies[:20]})
    
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
