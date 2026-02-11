# Movie Recommender Django Application

A Django-based movie recommendation web application using The Movie Database (TMDb) API.

> **🚀 Connected to GitHub & Render** - Auto-deploy enabled!

## Features

- Movie discovery with genre, language, and timeframe filters
- User authentication system
- Favorites, Watch Later, and Library lists
- Trending movies
- Detailed movie information with cast, crew, videos, and photos
- Person (actor/director) profiles
- Dark/Light theme toggle

## Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   Open your browser and go to `http://127.0.0.1:8000/`

## Configuration

The TMDb API key is configured in `movie_recommender/settings.py`. You can change it if needed:

```python
TMDB_API_KEY = 'your_api_key_here'
```

## Project Structure

```
movie_recommender/
├── manage.py
├── requirements.txt
├── README.md
├── movie_recommender/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── movies/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── movies/
│           └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## API Endpoints

### Authentication
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/signin/` - User login
- `POST /api/auth/signout/` - User logout

### Movies
- `GET /api/movies/discover/` - Discover movies with filters
- `GET /api/movies/trending/` - Get trending movies
- `GET /api/movies/<movie_id>/` - Get movie details

### User Lists (requires authentication)
- `GET /api/favorites/` - Get user's favorites
- `POST /api/favorites/add/` - Add to favorites
- `POST /api/favorites/remove/` - Remove from favorites
- `GET /api/watch-later/` - Get watch later list
- `POST /api/watch-later/add/` - Add to watch later
- `POST /api/watch-later/remove/` - Remove from watch later
- `GET /api/library/` - Get library
- `POST /api/library/add/` - Add to library
- `POST /api/library/remove/` - Remove from library

### Person
- `GET /api/person/<person_id>/` - Get person details

## Technologies Used

- Django 4.2+
- SQLite (default database)
- TMDb API
- Vanilla JavaScript
- HTML5/CSS3

## License

This project is for educational purposes.
