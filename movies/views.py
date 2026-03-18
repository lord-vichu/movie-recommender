import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Favorite, WatchLater, Library, UserRating
import json
import urllib.parse
import random
import time
from functools import lru_cache

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


DEFAULT_HTTP_HEADERS = {
    'User-Agent': 'CINE-M-AURA/1.0 (local development)',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}


def safe_external_get(url, params=None, timeout=10, retries=2, headers=None):
    merged_headers = DEFAULT_HTTP_HEADERS.copy()
    if headers:
        merged_headers.update(headers)

    retry_status_codes = {429, 500, 502, 503, 504}
    for attempt in range(retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=timeout
            )

            if response.status_code in retry_status_codes and attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue

            return response
        except requests.RequestException:
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue

    return None


def parse_omdb_runtime_minutes(runtime_value):
    if not runtime_value or runtime_value == 'N/A':
        return None

    try:
        return int(str(runtime_value).split()[0])
    except (ValueError, TypeError, IndexError):
        return None


@lru_cache(maxsize=2048)
def get_tmdb_imdb_id(movie_id):
    if not movie_id:
        return None

    try:
        response = safe_external_get(
            f'{settings.TMDB_BASE_URL}/movie/{movie_id}/external_ids',
            params={'api_key': settings.TMDB_API_KEY},
            timeout=8
        )

        if response and response.status_code == 200:
            return response.json().get('imdb_id')
    except Exception as error:
        print(f"TMDb external IDs error for {movie_id}: {error}")

    return None


@lru_cache(maxsize=4096)
def get_omdb_data_by_imdb_id(imdb_id):
    omdb_api_key = getattr(settings, 'OMDB_API_KEY', '')
    if not omdb_api_key or not imdb_id:
        return None

    try:
        response = safe_external_get(
            getattr(settings, 'OMDB_BASE_URL', 'https://www.omdbapi.com/'),
            params={
                'apikey': omdb_api_key,
                'i': imdb_id,
                'plot': 'short'
            },
            timeout=8
        )

        if not response or response.status_code != 200:
            return None

        data = response.json()
        if data.get('Response') != 'True':
            return None

        poster = data.get('Poster')
        if poster == 'N/A':
            poster = None

        imdb_rating = None
        if data.get('imdbRating') and data.get('imdbRating') != 'N/A':
            try:
                imdb_rating = float(data.get('imdbRating'))
            except (ValueError, TypeError):
                imdb_rating = None

        return {
            'imdb_id': data.get('imdbID') or imdb_id,
            'poster': poster,
            'plot': None if data.get('Plot') == 'N/A' else data.get('Plot'),
            'imdb_rating': imdb_rating,
            'imdb_votes': None if data.get('imdbVotes') == 'N/A' else data.get('imdbVotes'),
            'awards': None if data.get('Awards') == 'N/A' else data.get('Awards'),
            'runtime': parse_omdb_runtime_minutes(data.get('Runtime')),
            'rated': None if data.get('Rated') == 'N/A' else data.get('Rated')
        }
    except Exception as error:
        print(f"OMDb lookup error for {imdb_id}: {error}")

    return None


def enrich_tmdb_movie_with_omdb(movie_payload, tmdb_movie_id=None, imdb_id=None):
    if not movie_payload:
        return movie_payload

    omdb_api_key = getattr(settings, 'OMDB_API_KEY', '')
    if not omdb_api_key:
        return movie_payload

    should_try_omdb = (
        not movie_payload.get('poster') or
        not movie_payload.get('desc') or
        not movie_payload.get('rating')
    )
    if not should_try_omdb:
        return movie_payload

    if not imdb_id and tmdb_movie_id:
        imdb_id = get_tmdb_imdb_id(tmdb_movie_id)

    omdb_data = get_omdb_data_by_imdb_id(imdb_id)
    if not omdb_data:
        return movie_payload

    if not movie_payload.get('poster') and omdb_data.get('poster'):
        movie_payload['poster'] = omdb_data['poster']

    if not movie_payload.get('desc') and omdb_data.get('plot'):
        movie_payload['desc'] = omdb_data['plot']

    if not movie_payload.get('rating') and omdb_data.get('imdb_rating'):
        movie_payload['rating'] = omdb_data['imdb_rating']

    movie_payload['imdb_id'] = omdb_data.get('imdb_id')
    movie_payload['imdb_rating'] = omdb_data.get('imdb_rating')
    movie_payload['imdb_votes'] = omdb_data.get('imdb_votes')

    return movie_payload


def get_mock_movies(count=20, genre=None, language=None, search_query=None):
    """
    Provide mock movie data when external APIs are unavailable.
    This ensures the application remains functional for demonstration purposes.
    """
    mock_data = [
        {'id': 1, 'title': 'The Shawshank Redemption', 'year': 1994, 'genres': ['Drama'], 'lang': 'en', 'rating': 9.3, 'desc': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.'},
        {'id': 2, 'title': 'The Godfather', 'year': 1972, 'genres': ['Crime', 'Drama'], 'lang': 'en', 'rating': 9.2, 'desc': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.'},
        {'id': 3, 'title': 'The Dark Knight', 'year': 2008, 'genres': ['Action', 'Crime', 'Drama'], 'lang': 'en', 'rating': 9.0, 'desc': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests.'},
        {'id': 4, 'title': 'Pulp Fiction', 'year': 1994, 'genres': ['Crime', 'Drama'], 'lang': 'en', 'rating': 8.9, 'desc': 'The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.'},
        {'id': 5, 'title': 'Inception', 'year': 2010, 'genres': ['Action', 'Sci-Fi', 'Thriller'], 'lang': 'en', 'rating': 8.8, 'desc': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea.'},
        {'id': 6, 'title': 'Forrest Gump', 'year': 1994, 'genres': ['Drama', 'Romance'], 'lang': 'en', 'rating': 8.8, 'desc': 'The presidencies of Kennedy and Johnson, the Vietnam War, and other historical events unfold from the perspective of an Alabama man.'},
        {'id': 7, 'title': 'The Matrix', 'year': 1999, 'genres': ['Action', 'Sci-Fi'], 'lang': 'en', 'rating': 8.7, 'desc': 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.'},
        {'id': 8, 'title': 'Goodfellas', 'year': 1990, 'genres': ['Crime', 'Drama'], 'lang': 'en', 'rating': 8.7, 'desc': 'The story of Henry Hill and his life in the mob, covering his relationship with his wife and his partners in crime.'},
        {'id': 9, 'title': 'Interstellar', 'year': 2014, 'genres': ['Sci-Fi', 'Drama'], 'lang': 'en', 'rating': 8.6, 'desc': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity survival.'},
        {'id': 10, 'title': 'The Lion King', 'year': 1994, 'genres': ['Animation', 'Adventure', 'Drama'], 'lang': 'en', 'rating': 8.5, 'desc': 'Lion prince Simba flees his kingdom after the murder of his father, only to learn the true meaning of responsibility and bravery.'},
        {'id': 11, 'title': 'Gladiator', 'year': 2000, 'genres': ['Action', 'Drama'], 'lang': 'en', 'rating': 8.5, 'desc': 'A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.'},
        {'id': 12, 'title': 'The Prestige', 'year': 2006, 'genres': ['Drama', 'Mystery', 'Thriller'], 'lang': 'en', 'rating': 8.5, 'desc': 'After a tragic accident, two stage magicians engage in a battle to create the ultimate illusion while sacrificing everything they have.'},
        {'id': 13, 'title': 'The Departed', 'year': 2006, 'genres': ['Crime', 'Drama', 'Thriller'], 'lang': 'en', 'rating': 8.5, 'desc': 'An undercover cop and a mole in the police try to identify each other while infiltrating an Irish gang in Boston.'},
        {'id': 14, 'title': 'Whiplash', 'year': 2014, 'genres': ['Drama', 'Music'], 'lang': 'en', 'rating': 8.5, 'desc': 'A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor.'},
        {'id': 15, 'title': 'The Avengers', 'year': 2012, 'genres': ['Action', 'Sci-Fi'], 'lang': 'en', 'rating': 8.0, 'desc': 'Earth mightiest heroes must come together and learn to fight as a team to stop a villain from enslaving humanity.'},
        {'id': 16, 'title': 'Joker', 'year': 2019, 'genres': ['Crime', 'Drama', 'Thriller'], 'lang': 'en', 'rating': 8.4, 'desc': 'In Gotham City, mentally troubled comedian Arthur Fleck embarks on a downward spiral of revolution and bloody crime.'},
        {'id': 17, 'title': 'Parasite', 'year': 2019, 'genres': ['Comedy', 'Drama', 'Thriller'], 'lang': 'ko', 'rating': 8.6, 'desc': 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.'},
        {'id': 18, 'title': 'Dangal', 'year': 2016, 'genres': ['Action', 'Biography', 'Drama'], 'lang': 'hi', 'rating': 8.4, 'desc': 'Former wrestler Mahavir Singh Phogat trains his daughters to become world-class wrestlers.'},
        {'id': 19, 'title': '3 Idiots', 'year': 2009, 'genres': ['Comedy', 'Drama'], 'lang': 'hi', 'rating': 8.4, 'desc': 'Two friends embark on a quest for a lost buddy. On this journey, they encounter a long forgotten bet, a wedding they must crash, and a funeral that goes impossibly out of control.'},
        {'id': 20, 'title': 'Spider-Man: Into the Spider-Verse', 'year': 2018, 'genres': ['Animation', 'Action', 'Adventure'], 'lang': 'en', 'rating': 8.4, 'desc': 'Teen Miles Morales becomes Spider-Man of his reality, crossing paths with counterparts from other dimensions.'},
        {'id': 21, 'title': 'Avengers: Endgame', 'year': 2019, 'genres': ['Action', 'Sci-Fi'], 'lang': 'en', 'rating': 8.4, 'desc': 'After the devastating events of Infinity War, the Avengers assemble once more to reverse Thanos actions and restore balance to the universe.'},
        {'id': 22, 'title': 'The Conjuring', 'year': 2013, 'genres': ['Horror', 'Mystery', 'Thriller'], 'lang': 'en', 'rating': 7.5, 'desc': 'Paranormal investigators work to help a family terrorized by a dark presence in their farmhouse.'},
        {'id': 23, 'title': 'Get Out', 'year': 2017, 'genres': ['Horror', 'Mystery', 'Thriller'], 'lang': 'en', 'rating': 7.7, 'desc': 'A young African-American visits his white girlfriend family estate, where his simmering uneasiness becomes full-blown paranoia.'},
        {'id': 24, 'title': 'A Quiet Place', 'year': 2018, 'genres': ['Horror', 'Sci-Fi'], 'lang': 'en', 'rating': 7.5, 'desc': 'In a post-apocalyptic world, a family is forced to live in silence while hiding from monsters with ultra-sensitive hearing.'},
        {'id': 25, 'title': 'The Notebook', 'year': 2004, 'genres': ['Drama', 'Romance'], 'lang': 'en', 'rating': 7.8, 'desc': 'A poor yet passionate young man falls in love with a rich young woman, giving her a sense of freedom.'},
        {'id': 26, 'title': 'Titanic', 'year': 1997, 'genres': ['Drama', 'Romance'], 'lang': 'en', 'rating': 7.9, 'desc': 'A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.'},
        {'id': 27, 'title': 'La La Land', 'year': 2016, 'genres': ['Comedy', 'Drama', 'Romance'], 'lang': 'en', 'rating': 8.0, 'desc': 'While navigating their careers in Los Angeles, a pianist and an actress fall in love while attempting to reconcile their aspirations.'},
        {'id': 28, 'title': 'John Wick', 'year': 2014, 'genres': ['Action', 'Crime', 'Thriller'], 'lang': 'en', 'rating': 7.4, 'desc': 'An ex-hit-man comes out of retirement to track down the gangsters that killed his dog and took everything from him.'},
        {'id': 29, 'title': 'Mad Max: Fury Road', 'year': 2015, 'genres': ['Action', 'Sci-Fi'], 'lang': 'en', 'rating': 8.1, 'desc': 'In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland.'},
        {'id': 30, 'title': 'Toy Story', 'year': 1995, 'genres': ['Animation', 'Adventure', 'Comedy'], 'lang': 'en', 'rating': 8.3, 'desc': 'A cowboy doll is profoundly threatened when a new spaceman figure supplants him as top toy in a boy\'s room.'},
        # Malayalam Movies
        {'id': 31, 'title': 'Drishyam', 'year': 2013, 'genres': ['Thriller', 'Drama'], 'lang': 'ml', 'rating': 8.6, 'desc': 'A man goes to extreme lengths to save his family from the dark consequences of their actions.'},
        {'id': 32, 'title': 'Bangalore Days', 'year': 2014, 'genres': ['Drama', 'Romance', 'Comedy'], 'lang': 'ml', 'rating': 8.3, 'desc': 'Three cousins from Kerala relocate to Bangalore, continuing to harbor their dreams of a better life.'},
        {'id': 33, 'title': 'Premam', 'year': 2015, 'genres': ['Romance', 'Comedy', 'Drama'], 'lang': 'ml', 'rating': 8.3, 'desc': 'A young man falls in love three times over the course of his journey from school to college to his career.'},
        {'id': 34, 'title': 'Kumbalangi Nights', 'year': 2019, 'genres': ['Drama', 'Thriller'], 'lang': 'ml', 'rating': 8.7, 'desc': 'Four brothers living in the fishing hamlet of Kumbalangi share a love-hate relationship with each other.'},
        {'id': 35, 'title': 'Ustad Hotel', 'year': 2012, 'genres': ['Drama', 'Romance'], 'lang': 'ml', 'rating': 8.3, 'desc': 'A young man returns to Kerala after learning about the art of cooking from his grandfather.'},
        {'id': 36, 'title': 'Maheshinte Prathikaaram', 'year': 2016, 'genres': ['Drama', 'Comedy'], 'lang': 'ml', 'rating': 8.4, 'desc': 'A photographer in rural Kerala vows revenge after being publicly humiliated.'},
        {'id': 37, 'title': 'Angamaly Diaries', 'year': 2017, 'genres': ['Action', 'Drama'], 'lang': 'ml', 'rating': 8.0, 'desc': 'Vincent Pepe, a youngster with dreams of becoming a skilled gangster, navigates the dangerous world of pork trade.'},
        {'id': 38, 'title': 'Thondimuthalum Driksakshiyum', 'year': 2017, 'genres': ['Drama', 'Thriller'], 'lang': 'ml', 'rating': 8.2, 'desc': 'A newly married woman loses her gold chain on a bus, setting off an investigation.'},
        {'id': 39, 'title': 'Lucifer', 'year': 2019, 'genres': ['Action', 'Thriller'], 'lang': 'ml', 'rating': 7.8, 'desc': 'A political thriller about a power struggle for control after the death of a prominent political figure.'},
        {'id': 40, 'title': 'The Great Indian Kitchen', 'year': 2021, 'genres': ['Drama'], 'lang': 'ml', 'rating': 8.3, 'desc': 'A woman confronts the patriarchal traditions in her new marital home.'},
        # Tamil Movies
        {'id': 41, 'title': 'Vikram Vedha', 'year': 2017, 'genres': ['Action', 'Crime', 'Thriller'], 'lang': 'ta', 'rating': 8.4, 'desc': 'A fearless cop battles a clever gangster in this modern-day adaptation of the Vikramaditya-Betaal legend.'},
        {'id': 42, 'title': 'Kaala', 'year': 2018, 'genres': ['Action', 'Drama'], 'lang': 'ta', 'rating': 7.4, 'desc': 'A Dharavi-based crime lord who has risen from poverty stands up against a ruthless developer.'},
        {'id': 43, 'title': 'Super Deluxe', 'year': 2019, 'genres': ['Drama', 'Thriller'], 'lang': 'ta', 'rating': 8.3, 'desc': 'An unfaithful newly-wed wife, an estranged father, a priest and a transgender woman cross paths in Chennai.'},
        {'id': 44, 'title': 'Vada Chennai', 'year': 2018, 'genres': ['Action', 'Crime', 'Drama'], 'lang': 'ta', 'rating': 8.4, 'desc': 'A talented carrom player becomes embroiled in the criminal underworld of North Chennai.'},
        {'id': 45, 'title': 'Jai Bhim', 'year': 2021, 'genres': ['Drama', 'Crime'], 'lang': 'ta', 'rating': 8.8, 'desc': 'A tribal woman fights for justice for her missing husband with the help of an upright lawyer.'},
    ]
    
    # Filter by genre if specified
    if genre and genre != 'Any':
        filtered = [m for m in mock_data if genre.lower() in [g.lower() for g in m['genres']]]
        if filtered:
            mock_data = filtered
    
    # Filter by language if specified
    lang_map = {'English': 'en', 'Hindi': 'hi', 'Malayalam': 'ml', 'Tamil': 'ta', 'Korean': 'ko'}
    if language and language != 'Any' and language in lang_map:
        lang_code = lang_map[language]
        filtered = [m for m in mock_data if m['lang'] == lang_code]
        if filtered:
            mock_data = filtered
    
    # Filter by search query if specified
    if search_query:
        query_lower = search_query.lower()
        filtered = [m for m in mock_data if query_lower in m['title'].lower()]
        if filtered:
            mock_data = filtered
    
    # Shuffle and limit results
    random.shuffle(mock_data)
    result_movies = mock_data[:count]
    
    # Format results
    formatted = []
    for movie in result_movies:
        formatted.append({
            'id': movie['id'],
            'title': movie['title'],
            'year': movie['year'],
            'genres': movie['genres'],
            'lang': movie['lang'],
            'desc': movie['desc'],
            'poster': None,  # No poster URLs in mock data
            'rating': movie['rating'],
            'backdrop': None,
            'source': 'mock'
        })
    
    return formatted



def get_wikipedia_summary(search_term, wiki_lang='en'):
    """Fetch Wikipedia summary for a search term from specified language Wikipedia"""
    try:
        # Wikipedia API endpoint for specified language
        wiki_url = f"https://{wiki_lang}.wikipedia.org/api/rest_v1/page/summary/"
        encoded_term = urllib.parse.quote(search_term)
        
        response = safe_external_get(
            f"{wiki_url}{encoded_term}",
            timeout=5
        )

        if response and response.status_code == 200:
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


def search_wikipedia_movies(query, count=10, language_code='en'):
    """Search Wikipedia for movies and return formatted results with multiple strategies
    
    Args:
        query: Search query (e.g., 'malayalam', 'action', 'romance')
        count: Number of movies to return
        language_code: Wikipedia language code ('en' for English, 'ml' for Malayalam, 'ta' for Tamil, etc.)
    """
    try:
        import re

        movies = []
        seen_titles = set()

        index_like_terms = [
            'list of', 'films of', 'filmography', 'cinema of', 'film industry',
            'awards', 'category:', 'template:', 'portal:', 'disambiguation'
        ]

        non_movie_topic_terms = [
            'committee', 'federation', 'theatre', 'theater', 'festival',
            'society', 'studio', 'history of', 'culture of', 'cinema of'
        ]

        def is_index_page(title, description=''):
            title_lower = (title or '').lower()
            description_lower = (description or '').lower()

            if any(term in title_lower for term in index_like_terms):
                return True
            if any(term in description_lower for term in ['list of', 'film industry', 'overview of', 'history of']):
                return True
            if any(term in title_lower for term in non_movie_topic_terms):
                return True
            if any(term in description_lower for term in non_movie_topic_terms):
                return True
            if re.search(r'films? of \d{4}', title_lower):
                return True
            return False

        def looks_like_movie_page(title, description=''):
            title_lower = (title or '').lower()
            description_lower = (description or '').lower()

            if is_index_page(title, description):
                return False

            if re.search(r'\(\d{4}\s+film\)', title_lower):
                return True

            # Exclude biographies/organizations even if they mention film.
            if re.search(r'\bis an?\s+(indian\s+)?(actor|actress|director|producer|screenwriter|singer|politician|journalist|organization|association|award|festival)\b', description_lower):
                return False

            # Prefer encyclopedia-style movie summary lines.
            return bool(re.search(r'\bis an?\b[^\.]{0,120}\b(film|movie)\b', description_lower))
        
        # Determine which Wikipedia to search.
        # Keep English first for cleaner movie metadata, then regional wiki for extra coverage.
        wiki_languages = ['en']

        query_lower = query.lower()
        if ('malayalam' in query_lower or language_code == 'ml') and 'ml' not in wiki_languages:
            wiki_languages.append('ml')
        elif ('tamil' in query_lower or language_code == 'ta') and 'ta' not in wiki_languages:
            wiki_languages.append('ta')
        elif ('hindi' in query_lower or language_code == 'hi') and 'hi' not in wiki_languages:
            wiki_languages.append('hi')
        elif ('korean' in query_lower or language_code == 'ko') and 'ko' not in wiki_languages:
            wiki_languages.append('ko')
        
        # Search across different language Wikipedias
        for wiki_lang in wiki_languages:
            if len(movies) >= count:
                break
                
            search_url = f"https://{wiki_lang}.wikipedia.org/w/api.php"
            
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
                    
                    response = safe_external_get(search_url, params=search_params, timeout=10)
                    if not response or response.status_code != 200:
                        continue
                    
                    search_results = response.json()
                    titles = search_results[1] if len(search_results) > 1 else []
                    descriptions = search_results[2] if len(search_results) > 2 else []
                    urls = search_results[3] if len(search_results) > 3 else []
                    
                    for idx, title in enumerate(titles):
                        if len(movies) >= count:
                            break
                            
                        if title.lower() in seen_titles:
                            continue
                        
                        if looks_like_movie_page(title, descriptions[idx] if idx < len(descriptions) else ''):
                            seen_titles.add(title.lower())
                            
                            year_match = re.search(r'\((\d{4})', title)
                            year = int(year_match.group(1)) if year_match else None

                            clean_title = re.sub(r'\s*\((\d{4})\s+film\)\s*', '', title, flags=re.IGNORECASE).strip()
                            if clean_title == title:
                                clean_title = re.sub(r'\s*\((\d{4})\)\s*', '', title).strip()
                            description = descriptions[idx] if idx < len(descriptions) else ''
                            article_url = urls[idx] if idx < len(urls) else ''

                            movies.append({
                                'id': f"wiki_{title.replace(' ', '_')}",
                                'title': clean_title,
                                'year': year,
                                'genres': [],
                                'lang': wiki_lang,
                                'desc': description or 'No description available.',
                                'poster': None,
                                'rating': None,
                                'backdrop': None,
                                'source': 'wikipedia',
                                'wiki_url': article_url,
                                'wiki_lang': wiki_lang
                            })
                                
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
                        
                        cat_response = safe_external_get(search_url, params=category_params, timeout=10)
                        if cat_response and cat_response.status_code == 200:
                            cat_data = cat_response.json()
                            members = cat_data.get('query', {}).get('categorymembers', [])
                            
                            for member in members:
                                if len(movies) >= count:
                                    break
                                
                                member_title = member.get('title', '')
                                if member_title.lower() in seen_titles:
                                    continue
                                
                                if is_index_page(member_title):
                                    continue

                                seen_titles.add(member_title.lower())

                                year_match = re.search(r'\((\d{4})', member_title)
                                year = int(year_match.group(1)) if year_match else None

                                clean_title = re.sub(r'\s*\((\d{4})\s+film\)\s*', '', member_title, flags=re.IGNORECASE).strip()
                                if clean_title == member_title:
                                    clean_title = re.sub(r'\s*\((\d{4})\)\s*', '', member_title).strip()

                                movies.append({
                                    'id': f"wiki_{member_title.replace(' ', '_')}",
                                    'title': clean_title,
                                    'year': year,
                                    'genres': [],
                                    'lang': wiki_lang,
                                    'desc': 'From Wikipedia category listing.',
                                    'poster': None,
                                    'rating': None,
                                    'backdrop': None,
                                    'source': 'wikipedia',
                                    'wiki_url': f"https://{wiki_lang}.wikipedia.org/wiki/{urllib.parse.quote(member_title.replace(' ', '_'))}",
                                    'wiki_lang': wiki_lang
                                })
                                    
                    except Exception as cat_err:
                        print(f"Wikipedia category search error for '{cat_name}': {cat_err}")
                        continue
        
        print(f"Wikipedia search for '{query}' returned {len(movies)} movies")
        return movies[:count]
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []


def search_wikipedia_language_movies(language_name, count=20):
    """Fetch movie pages from language-specific Wikipedia film categories (higher quality than broad search)."""
    try:
        import re

        lang_to_code = {
            'English': 'en',
            'Hindi': 'hi',
            'Malayalam': 'ml',
            'Tamil': 'ta',
            'Korean': 'ko',
        }

        category_map = {
            'English': ['English-language films', 'American films', 'British films'],
            'Hindi': ['Hindi-language films', 'Hindi films', 'Bollywood films', 'Indian Hindi-language films'],
            'Malayalam': ['Malayalam-language films', 'Malayalam films', 'Malayalam cinema'],
            'Tamil': ['Tamil-language films', 'Tamil films', 'Tamil cinema'],
            'Korean': ['Korean-language films', 'South Korean films'],
        }

        if language_name not in category_map:
            return []

        wiki_lang = 'en'
        movies = []
        seen_titles = set()
        search_url = f"https://{wiki_lang}.wikipedia.org/w/api.php"

        for category_name in category_map[language_name]:
            if len(movies) >= count:
                break

            params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{category_name}',
                'cmnamespace': 0,
                'cmtype': 'page',
                'cmlimit': min(max(count * 4, 50), 500),
                'format': 'json',
            }

            response = safe_external_get(search_url, params=params, timeout=10)
            if not response or response.status_code != 200:
                continue

            members = response.json().get('query', {}).get('categorymembers', [])
            for member in members:
                if len(movies) >= count:
                    break

                title = (member.get('title') or '').strip()
                title_lower = title.lower()
                if not title or title_lower in seen_titles:
                    continue

                if ('list of' in title_lower or
                    'lists of' in title_lower or
                        re.search(r'films? of \d{4}', title_lower) or
                        'awards' in title_lower or
                        'filmfare' in title_lower or
                    'cinema of' in title_lower or
                    'pornography' in title_lower or
                    'film movement' in title_lower or
                    'movement' in title_lower):
                    continue

                seen_titles.add(title_lower)
                year_match = re.search(r'\((\d{4})', title)
                year = int(year_match.group(1)) if year_match else None

                clean_title = re.sub(r'\s*\((\d{4})\s+film\)\s*', '', title, flags=re.IGNORECASE).strip()
                if clean_title == title:
                    clean_title = re.sub(r'\s*\((\d{4})\)\s*', '', title).strip()

                movies.append({
                    'id': f"wiki_{title.replace(' ', '_')}",
                    'title': clean_title,
                    'year': year,
                    'genres': [],
                    'lang': lang_to_code.get(language_name, 'en'),
                    'desc': f"From Wikipedia category: {category_name}",
                    'poster': None,
                    'rating': None,
                    'backdrop': None,
                    'source': 'wikipedia',
                    'wiki_url': f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                    'wiki_lang': 'en',
                })

        if len(movies) < count and language_name in {'Hindi', 'Malayalam', 'Tamil'}:
            fallback_query = f"{language_name.lower()} film"
            fallback_movies = search_wikipedia_movies(fallback_query, count - len(movies), 'en')
            for movie in fallback_movies:
                movie_key = (movie.get('source'), str(movie.get('id')), (movie.get('title') or '').lower())
                existing_keys = {(m.get('source'), str(m.get('id')), (m.get('title') or '').lower()) for m in movies}
                if movie_key not in existing_keys:
                    movies.append(movie)
                if len(movies) >= count:
                    break

        return movies[:count]
    except Exception as error:
        print(f"Wikipedia language category search error: {error}")
        return []


def landing(request):
    """Landing page view - shown to non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('movies:index')
    return render(request, 'movies/landing.html')


@login_required
def index(request):
    """Main page view - requires authentication"""
    return render(request, 'movies/index.html')


@require_http_methods(["POST"])
@csrf_exempt
def user_signup(request):
    """User registration"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        if len(password) < 4:
            return JsonResponse({'error': 'Password must be at least 4 characters'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken'}, status=400)
        
        # Create user without requiring additional permissions
        user = User.objects.create_user(
            username=username,
            password=password
        )
        
        # Log the user in immediately after signup
        from django.contrib.auth import load_backend
        backend = load_backend('django.contrib.auth.backends.ModelBackend')
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'username': username,
            'message': 'Account created successfully'
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"Signup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Failed to create account: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
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
@csrf_exempt
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
        search_query = request.GET.get('search', '').strip()
        cert = request.GET.get('cert', 'Any')
        sort_by = request.GET.get('sort_by', 'none')
        
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

        wiki_lang_codes = {
            'English': 'en', 'Hindi': 'hi', 'Malayalam': 'ml',
            'Tamil': 'ta', 'Korean': 'ko'
        }

        def detect_search_language(query_text, selected_language):
            if selected_language in wiki_lang_codes:
                return wiki_lang_codes[selected_language], selected_language.lower(), True

            query_lower = (query_text or '').lower()
            language_keywords = {
                'Malayalam': ['malayalam', 'malayali', 'മലയാളം'],
                'Tamil': ['tamil', 'kollywood', 'தமிழ்'],
                'Hindi': ['hindi', 'bollywood', 'हिंदी'],
                'Korean': ['korean', 'k-movie', 'kmovie']
            }

            for language_name, keywords in language_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    return wiki_lang_codes[language_name], language_name.lower(), True

            if 'any language' in query_lower or 'all language' in query_lower:
                return 'en', 'any language', True

            return 'en', 'english', False
        
        # If there's a specific search query, use aggressive fuzzy matching
        if search_query:
            tmdb_results = []
            search_terms = [search_query]
            search_wiki_lang, search_lang_name, prefer_wikipedia = detect_search_language(search_query, language)
            
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
            
            # Try to search TMDb with all variations (limit to first 10 terms to avoid too many requests)
            # If TMDb is unavailable, we'll fallback to Wikipedia
            seen_ids = set()
            tmdb_available = True
            for term in search_terms[:10]:
                if not tmdb_available:
                    break
                try:
                    # Search multiple pages for each term
                    for page in range(1, 3):  # Search 2 pages per term
                        search_response = safe_external_get(
                            f'{settings.TMDB_BASE_URL}/search/movie',
                            params={
                                'api_key': settings.TMDB_API_KEY,
                                'query': term,
                                'page': page
                            },
                            timeout=10
                        )
                        
                        if not search_response:
                            tmdb_available = False
                            break

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
                    print(f"TMDb search error for term '{term}': {e}")
                    # Mark TMDb as unavailable and break out to use Wikipedia
                    tmdb_available = False
                    break
                
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
                movie_payload = {
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
                }

                movies.append(enrich_tmdb_movie_with_omdb(movie_payload, tmdb_movie_id=movie.get('id')))
            
            # Use Wikipedia more aggressively for language-intent searches.
            # Keep Wikipedia results first so they are not hidden by TMDb slicing.
            wiki_movies = []
            if prefer_wikipedia:
                inferred_language_name = {
                    'english': 'English',
                    'hindi': 'Hindi',
                    'malayalam': 'Malayalam',
                    'tamil': 'Tamil',
                    'korean': 'Korean',
                }.get(search_lang_name)
                category_language = language if language in wiki_lang_codes else inferred_language_name

                # Category-based lookup is more reliable for language-specific searches
                # (especially Malayalam/Tamil/Hindi) than plain text opensearch.
                if category_language:
                    wiki_movies.extend(search_wikipedia_language_movies(category_language, count * 2))

                wiki_movies.extend(search_wikipedia_movies(search_query, count * 2, search_wiki_lang))

                if len(wiki_movies) < count:
                    wiki_movies.extend(search_wikipedia_movies(f"{search_lang_name} movies", count, search_wiki_lang))
                if len(wiki_movies) < count:
                    wiki_movies.extend(search_wikipedia_movies(f"{search_lang_name} cinema", count, search_wiki_lang))
                if len(wiki_movies) < count:
                    wiki_movies.extend(search_wikipedia_movies(f"{search_lang_name} film", count, 'en'))
                if len(wiki_movies) < count:
                    wiki_movies.extend(search_wikipedia_movies(f"{search_lang_name} films", count, 'en'))
            elif len(movies) < count:
                wiki_movies.extend(search_wikipedia_movies(search_query, count - len(movies), search_wiki_lang))

            # Final guardrail for language searches: if fuzzy title search misses,
            # still return category-backed language results instead of empty payloads.
            if prefer_wikipedia and language in wiki_lang_codes and len(wiki_movies) == 0:
                wiki_movies.extend(search_wikipedia_language_movies(language, max(count, 20)))

            if wiki_movies:
                combined_movies = []
                seen_movie_keys = set()
                ordered_candidates = wiki_movies + movies if prefer_wikipedia else movies + wiki_movies

                for movie in ordered_candidates:
                    movie_key = (movie.get('source'), str(movie.get('id')), (movie.get('title') or '').lower())
                    if movie_key in seen_movie_keys:
                        continue
                    seen_movie_keys.add(movie_key)
                    combined_movies.append(movie)

                movies = combined_movies

            # Post-filter search results by timeframe only.
            # Language is already handled by routing to language-specific Wikipedia above.
            if timeframe == 'old':
                movies = [m for m in movies if m.get('year') and m['year'] <= 2009]
            elif timeframe == 'new':
                movies = [m for m in movies if m.get('year') and m['year'] >= 2011]
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

            # Certificate filter
            india_certs = {'U', 'UA', 'A'}
            us_certs = {'PG-13', 'R', 'Not Rated'}
            if cert != 'Any':
                if cert in india_certs:
                    params['certification_country'] = 'IN'
                    params['certification'] = cert
                elif cert in us_certs:
                    params['certification_country'] = 'US'
                    params['certification'] = cert
            
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
            
            # Try to fetch multiple pages from TMDb
            pages = min(15, max(1, count // 20))
            all_movies = []
            tmdb_available = True
            
            try:
                for page in range(1, pages + 1):
                    params['page'] = page
                    response = safe_external_get(
                        f'{settings.TMDB_BASE_URL}/discover/movie',
                        params=params,
                        timeout=10
                    )
                    
                    if not response:
                        tmdb_available = False
                        break

                    if response.status_code == 200:
                        data = response.json()
                        all_movies.extend(data.get('results', []))
            except Exception as e:
                print(f"TMDb discover error: {e}")
                # Mark TMDb as unavailable and continue with Wikipedia fallback
                tmdb_available = False
            
            # Format movies
            for movie in all_movies[:count]:
                movie_payload = {
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
                }

                movies.append(enrich_tmdb_movie_with_omdb(movie_payload, tmdb_movie_id=movie.get('id')))
            
            # Always try to supplement with Wikipedia if we don't have enough movies,
            # and ALWAYS use Wikipedia when a specific language filter is selected.
            remaining_count = count - len(movies)
            print(f"TMDb returned {len(movies)} movies, need {remaining_count} more")

            wiki_movies_collected = []
            force_language_wiki = language != 'Any'

            if force_language_wiki or not tmdb_available or remaining_count > 0:
                if language != 'Any':
                    language_names = {
                        'English': 'english', 'Hindi': 'hindi', 'Malayalam': 'malayalam',
                        'Tamil': 'tamil', 'Korean': 'korean'
                    }

                    if language in language_names:
                        lang_name = language_names[language]
                        wiki_lang_code = wiki_lang_codes.get(language, 'en')
                        fallback_wiki_lang = 'en'
                        wiki_count_needed = max(count, max(1, remaining_count) * 2)
                        print(f"Searching Wikipedia ({wiki_lang_code}) for {wiki_count_needed} {lang_name} movies")

                        # Priority 1: high-quality category-based pages.
                        category_movies = search_wikipedia_language_movies(language, wiki_count_needed)
                        print(f"Wikipedia category search for {language} returned {len(category_movies)} movies")
                        wiki_movies_collected.extend(category_movies)

                        # If category lookup produced movies, prefer quality over noisy broad searches.
                        if len(wiki_movies_collected) > 0:
                            search_terms = []
                        else:
                            search_terms = [
                                f"{lang_name} film",
                                f"{lang_name} films",
                                f"{lang_name} movie",
                                f"{lang_name}-language",
                                f"{lang_name} movies",
                                f"{lang_name} cinema",
                            ]

                        for search_term in search_terms:
                            if len(wiki_movies_collected) >= count:
                                break
                            wiki_movies = search_wikipedia_movies(search_term, wiki_count_needed, fallback_wiki_lang)
                            print(f"Wikipedia search '{search_term}' returned {len(wiki_movies)} movies")
                            wiki_movies_collected.extend(wiki_movies)

                # If genre was selected and we still need more, search Wikipedia
                if selected_genre_name and selected_genre_name != 'Any':
                    genre_wiki_needed = max(count - len(wiki_movies_collected), max(remaining_count, 0))
                    if genre_wiki_needed > 0:
                        wiki_query = f"{selected_genre_name.lower()}"
                        print(f"Searching Wikipedia for {genre_wiki_needed} {wiki_query} movies")
                        wiki_movies = search_wikipedia_movies(wiki_query, genre_wiki_needed * 2, 'en')
                        wiki_movies_collected.extend(wiki_movies)

                # If still no movies, provide some default Wikipedia content
                if len(movies) == 0 and len(wiki_movies_collected) == 0:
                    print("No movies from TMDb or filters, getting default Wikipedia movies")
                    default_searches = ['popular films', '2024 films', 'cinema']
                    for search_term in default_searches:
                        if len(wiki_movies_collected) >= count:
                            break
                        wiki_movies = search_wikipedia_movies(search_term, count, 'en')
                        wiki_movies_collected.extend(wiki_movies)

            if wiki_movies_collected:
                combined_movies = []
                seen_movie_keys = set()
                ordered_candidates = wiki_movies_collected + movies if force_language_wiki else movies + wiki_movies_collected

                for movie in ordered_candidates:
                    movie_key = (movie.get('source'), str(movie.get('id')), (movie.get('title') or '').lower())
                    if movie_key in seen_movie_keys:
                        continue
                    seen_movie_keys.add(movie_key)
                    combined_movies.append(movie)

                movies = combined_movies
        
        print(f"Final movie count: {len(movies)}")
        
        # Do not return mock data from API endpoints.
        if len(movies) == 0:
            return JsonResponse(
                {'error': 'No movies available from TMDb/Wikipedia right now. Please try again in a moment.'},
                status=503
            )
        
        # Apply sort before slicing
        if sort_by == 'year_desc':
            movies.sort(key=lambda m: m.get('year') or 0, reverse=True)
        elif sort_by == 'year_asc':
            movies.sort(key=lambda m: m.get('year') or 0)
        elif sort_by == 'rating_desc':
            movies.sort(key=lambda m: m.get('rating') or 0, reverse=True)
        elif sort_by == 'rating_asc':
            movies.sort(key=lambda m: m.get('rating') or 0)

        return JsonResponse({'movies': movies[:count]})  # Limit to requested count
    
    except Exception as e:
        print(f"Error in discover_movies: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_trending(request):
    """Get trending movies from TMDb and popular movies from Wikipedia"""
    
    def normalize_title(title):
        """Normalize title for comparison by removing extra whitespace and converting to lowercase"""
        if not title:
            return ''
        # Convert to lowercase, normalize whitespace (replace multiple spaces with single space)
        import re
        normalized = re.sub(r'\s+', ' ', title.lower().strip())
        return normalized
    
    try:
        movies = []
        seen_titles = set()  # Track unique movie titles to prevent duplicates
        seen_ids = set()  # Track unique movie IDs to prevent duplicates
        
        # Try to get TMDb trending movies
        try:
            response = safe_external_get(
                f'{settings.TMDB_BASE_URL}/trending/movie/day',
                params={'api_key': settings.TMDB_API_KEY},
                timeout=10
            )
            
            if response and response.status_code == 200:
                data = response.json()
                
                for movie in data.get('results', [])[:15]:
                    movie_id = movie.get('id')
                    movie_title = normalize_title(movie.get('title') or movie.get('original_title', ''))
                    
                    # Skip if we've already seen this movie (by ID or title)
                    if movie_id in seen_ids or movie_title in seen_titles:
                        continue
                    
                    seen_ids.add(movie_id)
                    seen_titles.add(movie_title)
                    
                    movie_payload = {
                        'id': movie_id,
                        'title': movie.get('title') or movie.get('original_title'),
                        'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
                        'poster': f"{settings.TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get('poster_path') else None,
                        'rating': round(movie.get('vote_average', 0), 1) if movie.get('vote_average') else None,
                        'source': 'tmdb'
                    }

                    movies.append(enrich_tmdb_movie_with_omdb(movie_payload, tmdb_movie_id=movie_id))
        except Exception as tmdb_err:
            print(f"TMDb trending fetch error: {tmdb_err}")
            # Continue to Wikipedia fallback
        
        # Add Wikipedia movies to supplement or replace TMDb results if unavailable
        try:
            # Request more if we don't have enough from TMDb
            needed = max(20 - len(movies), 10)
            wiki_search_terms = ['2024 films', '2025 films', 'blockbuster films', 'popular films']
            for term in wiki_search_terms:
                if len(movies) >= 20:
                    break
                wiki_movies = search_wikipedia_movies(term, needed, 'en')
                
                # Add only unique movies from Wikipedia
                for wiki_movie in wiki_movies:
                    if len(movies) >= 20:
                        break
                    
                    wiki_title = normalize_title(wiki_movie.get('title', ''))
                    wiki_id = wiki_movie.get('id')
                    
                    # Skip if we've already seen this movie
                    if wiki_title in seen_titles or wiki_id in seen_ids:
                        continue
                    
                    seen_titles.add(wiki_title)
                    seen_ids.add(wiki_id)
                    movies.append(wiki_movie)
        except Exception as wiki_err:
            print(f"Wikipedia trending fetch error: {wiki_err}")
        
        # Do not return mock data from API endpoints.
        if len(movies) == 0:
            return JsonResponse(
                {'error': 'Trending is temporarily unavailable from external providers. Please retry shortly.'},
                status=503
            )
        
        return JsonResponse({'trending': movies[:20]})
    
    except Exception as e:
        print(f"Error in get_trending: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_movie_details(request, movie_id):
    """Get detailed movie information"""
    try:
        # Try to get movie details from TMDb
        try:
            response = safe_external_get(
                f'{settings.TMDB_BASE_URL}/movie/{movie_id}',
                params={
                    'api_key': settings.TMDB_API_KEY,
                    'append_to_response': 'credits,videos,images,similar,release_dates'
                },
                timeout=10
            )
            
            if not response:
                return JsonResponse({'error': 'Unable to fetch movie details. TMDb API is unavailable.'}, status=503)

            if response.status_code != 200:
                return JsonResponse({'error': 'Movie not found'}, status=404)
            
            movie = response.json()
        except Exception as tmdb_err:
            print(f"TMDb movie details fetch error: {tmdb_err}")
            return JsonResponse({'error': 'Unable to fetch movie details. TMDb API is unavailable.'}, status=503)
        
        # Format response
        data = {
            'id': movie.get('id'),
            'title': movie.get('title'),
            'year': int(movie.get('release_date', '0000')[:4]) if movie.get('release_date') else None,
            'desc': movie.get('overview'),
            'imdb_id': movie.get('imdb_id'),
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
            'omdb': None,
            'wikipedia': None
        }

        # Optional OMDb enrichment for missing poster/overview/rating + extra metadata.
        data = enrich_tmdb_movie_with_omdb(data, tmdb_movie_id=movie.get('id'), imdb_id=movie.get('imdb_id'))
        omdb_data = get_omdb_data_by_imdb_id(data.get('imdb_id'))
        if omdb_data:
            data['omdb'] = omdb_data
            if not data.get('runtime') and omdb_data.get('runtime'):
                data['runtime'] = omdb_data.get('runtime')
            if omdb_data.get('awards'):
                data['awards'] = omdb_data.get('awards')
        
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
        # Try to get person details from TMDb
        try:
            response = safe_external_get(
                f'{settings.TMDB_BASE_URL}/person/{person_id}',
                params={
                    'api_key': settings.TMDB_API_KEY,
                    'append_to_response': 'movie_credits'
                },
                timeout=10
            )
            
            if not response:
                return JsonResponse({'error': 'Unable to fetch person details. TMDb API is unavailable.'}, status=503)

            if response.status_code != 200:
                return JsonResponse({'error': 'Person not found'}, status=404)
            
            person = response.json()
        except Exception as tmdb_err:
            print(f"TMDb person details fetch error: {tmdb_err}")
            return JsonResponse({'error': 'Unable to fetch person details. TMDb API is unavailable.'}, status=503)
        
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
