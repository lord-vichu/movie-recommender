// Movie Recommender Django App - Client Side JavaScript
'use strict';

// Helper function to get CSRF token
function getCSRFToken() {
    return window.CSRF_TOKEN;
}

// Helper function for API calls
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    return response.json();
}

// DOM elements
const genreEl = document.getElementById('genre');
const langEl = document.getElementById('language');
const certEl = document.getElementById('certSelect');
const countEl = document.getElementById('count');
const searchEl = document.getElementById('searchTerm');
const sortEl = document.getElementById('sortBy');
const recommendBtn = document.getElementById('recommend');
const surpriseBtn = document.getElementById('surprise');
const searchBtn = document.getElementById('searchBtn');
const voiceSearchBtn = document.getElementById('voiceSearchBtn');
const favoritesBtn = document.getElementById('favoritesBtn');
const watchLaterBtn = document.getElementById('watchLaterBtn');
const libraryBtn = document.getElementById('libraryBtn');
const trendingBtn = document.getElementById('trendingBtn');
const resultsEl = document.getElementById('results');
const errorContainer = document.getElementById('errorContainer');
const themeToggleBtn = document.getElementById('themeToggle');

console.log('DOM Elements loaded:', {
    genreEl: !!genreEl,
    langEl: !!langEl,
    recommendBtn: !!recommendBtn,
    resultsEl: !!resultsEl,
    errorContainer: !!errorContainer
});

// Theme handling
function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');
    if (themeToggleBtn) themeToggleBtn.textContent = theme === 'light' ? '☀️' : '🌙';
    localStorage.setItem('movie_theme', theme);
}

// Initialize theme
const storedTheme = localStorage.getItem('movie_theme');
let theme = storedTheme;
if (!theme) {
    theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}
applyTheme(theme);

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const current = document.body.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        applyTheme(current === 'light' ? 'dark' : 'light');
    });
}

// Error display
function showError(message) {
    if (!errorContainer) return;
    errorContainer.textContent = message;
    errorContainer.classList.add('show');
    setTimeout(() => {
        errorContainer.classList.remove('show');
    }, 5000);
}

function clearError() {
    if (errorContainer) {
        errorContainer.classList.remove('show');
        errorContainer.textContent = '';
    }
}

// Auth UI update
function updateUserUI() {
    const btn = document.getElementById('signInBtn');
    const label = document.getElementById('userLabel');
    
    if (window.IS_AUTHENTICATED && btn) {
        btn.textContent = 'Sign out';
        btn.onclick = (e) => { e.preventDefault(); signOut(); };
        if (label) label.textContent = window.USERNAME || '';
    } else if (btn) {
        btn.textContent = 'Sign in';
        btn.onclick = (e) => { e.preventDefault(); openSignInModal(); };
        if (label) label.textContent = '';
    }
}

// Sign in modal
function openSignInModal() {
    const overlay = document.getElementById('signInOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function closeSignInModal() {
    const overlay = document.getElementById('signInOverlay');
    if (overlay) overlay.style.display = 'none';
    document.getElementById('signUser').value = '';
    document.getElementById('signPass').value = '';
}

async function signOut() {
    try {
        await apiCall('/api/auth/signout/', 'POST');
        window.IS_AUTHENTICATED = false;
        window.USERNAME = '';
        updateUserUI();
        showError('Signed out');
        window.location.reload();
    } catch (err) {
        showError('Sign out failed');
    }
}

async function doSignIn() {
    try {
        const username = document.getElementById('signUser').value.trim();
        const password = document.getElementById('signPass').value;
        
        if (!username || !password) {
            showError('Enter username and password');
            return;
        }
        
        const result = await apiCall('/api/auth/signin/', 'POST', { username, password });
        
        if (result.error) {
            showError(result.error);
        } else {
            window.IS_AUTHENTICATED = true;
            window.USERNAME = username;
            updateUserUI();
            closeSignInModal();
            showError(`Signed in as ${username}`);
            window.location.reload();
        }
    } catch (err) {
        showError('Sign in failed');
    }
}

async function doSignUp() {
    try {
        const username = document.getElementById('signUser').value.trim();
        const password = document.getElementById('signPass').value;
        
        if (!username || !password) {
            showError('Enter username and password');
            return;
        }
        
        const result = await apiCall('/api/auth/signup/', 'POST', { username, password });
        
        if (result.error) {
            showError(result.error);
        } else {
            window.IS_AUTHENTICATED = true;
            window.USERNAME = username;
            updateUserUI();
            closeSignInModal();
            showError(`Account created for ${username}`);
            window.location.reload();
        }
    } catch (err) {
        showError('Sign up failed');
    }
}

// Wire auth buttons
document.getElementById('signInSubmit')?.addEventListener('click', doSignIn);
document.getElementById('signUpSubmit')?.addEventListener('click', doSignUp);
document.getElementById('signClose')?.addEventListener('click', closeSignInModal);

updateUserUI();

// Movie rendering
function renderResults(movies) {
    if (!resultsEl) return;
    
    if (!movies || movies.length === 0) {
        resultsEl.innerHTML = '<div class="no-results">No movies found. Try different filters.</div>';
        // Show results section even with no results
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }
        return;
    }
    
    // Show results section and update count
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = `${movies.length} ${movies.length === 1 ? 'movie' : 'movies'} found`;
        }
    }
    
    resultsEl.innerHTML = '';
    
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.cursor = 'pointer';
        
        const poster = document.createElement('div');
        poster.className = 'poster';
        if (movie.poster) {
            const img = document.createElement('img');
            img.src = movie.poster;
            img.alt = movie.title;
            img.loading = 'lazy';
            poster.appendChild(img);
        } else {
            poster.textContent = movie.title;
        }
        
        const meta = document.createElement('div');
        meta.className = 'meta';
        
        const title = document.createElement('h3');
        title.textContent = movie.title;
        if (movie.year) title.textContent += ` (${movie.year})`;
        
        if (movie.rating) {
            const rating = document.createElement('span');
            rating.className = 'rating';
            rating.textContent = `⭐ ${movie.rating}`;
            title.appendChild(rating);
        }
        
        // Add Wikipedia badge if source is Wikipedia
        if (movie.source === 'wikipedia') {
            const wikiBadge = document.createElement('span');
            wikiBadge.className = 'chip';
            wikiBadge.textContent = '📖 Wikipedia';
            wikiBadge.style.background = 'rgba(66, 133, 244, 0.15)';
            wikiBadge.style.color = '#4285f4';
            title.appendChild(wikiBadge);
        }
        
        const desc = document.createElement('p');
        desc.textContent = movie.desc || 'No description available.';
        
        meta.appendChild(title);
        meta.appendChild(desc);
        
        card.appendChild(poster);
        card.appendChild(meta);
        
        card.addEventListener('click', () => openQuickView(movie, card));
        
        resultsEl.appendChild(card);
    });
}

// Sort movies based on selected criteria
function sortMovies(movies, sortBy) {
    const sorted = [...movies]; // Create a copy
    
    switch(sortBy) {
        case 'year_desc':
            return sorted.sort((a, b) => (b.year || 0) - (a.year || 0));
        case 'year_asc':
            return sorted.sort((a, b) => (a.year || 0) - (b.year || 0));
        case 'rating_desc':
            return sorted.sort((a, b) => {
                const ratingA = parseFloat(a.rating) || 0;
                const ratingB = parseFloat(b.rating) || 0;
                return ratingB - ratingA;
            });
        case 'rating_asc':
            return sorted.sort((a, b) => {
                const ratingA = parseFloat(a.rating) || 0;
                const ratingB = parseFloat(b.rating) || 0;
                return ratingA - ratingB;
            });
        case 'none':
        default:
            // Shuffle for random order
            for (let i = sorted.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [sorted[i], sorted[j]] = [sorted[j], sorted[i]];
            }
            return sorted;
    }
}

// Discover movies
async function discoverMovies() {
    try {
        console.log('discoverMovies called');
        clearError();
        resultsEl.innerHTML = '<div class="loading-container"><div class="movie-loader">MOVIE RECOMMENDER<span class="loading-dots"><span>.</span><span>.</span><span>.</span></span></div></div>';
        
        const genre = genreEl.value;
        const language = langEl.value;
        const timeframe = document.querySelector('input[name="timeframe"]:checked')?.value || 'any';
        const count = parseInt(countEl.value) || 20;
        const searchTerm = searchEl.value.trim();
        const sortBy = sortEl.value;
        
        console.log('Filters:', { genre, language, timeframe, count, searchTerm, sortBy });
        
        const params = new URLSearchParams({
            genre,
            language,
            timeframe,
            count: count.toString()
        });
        
        // Add search parameter if present
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        
        const url = `/api/movies/discover/?${params}`;
        console.log('Fetching:', url);
        
        const result = await apiCall(url);
        
        console.log('API result:', result);
        
        if (result.error) {
            showError(result.error);
            resultsEl.innerHTML = '';
        } else {
            let movies = result.movies || [];
            
            // Apply sorting
            if (sortBy && sortBy !== 'none') {
                movies = sortMovies(movies, sortBy);
                console.log(`Sorted by ${sortBy}`);
            }
            
            renderResults(movies);
        }
    } catch (err) {
        console.error('discoverMovies error:', err);
        showError('Failed to load movies: ' + err.message);
        resultsEl.innerHTML = '';
    }
}

// Load trending
async function loadTrending() {
    try {
        const result = await apiCall('/api/movies/trending/');
        const trendingList = document.getElementById('trendingList');
        
        if (!trendingList) return;
        
        if (result.error || !result.trending) {
            trendingList.innerHTML = '<div style="color:var(--muted)">Unable to load trending movies</div>';
            return;
        }
        
        trendingList.innerHTML = '';
        
        // Create cards
        const createCard = (movie) => {
            const card = document.createElement('div');
            card.className = 'trending-card';
            card.style.cursor = 'pointer';
            
            // Handle poster - use placeholder if null
            if (movie.poster) {
                const img = document.createElement('img');
                img.src = movie.poster;
                img.alt = movie.title;
                img.loading = 'lazy';
                card.appendChild(img);
            } else {
                // Create a placeholder div with movie title
                const placeholder = document.createElement('div');
                placeholder.className = 'poster-placeholder';
                placeholder.style.cssText = 'width:100%;height:200px;background:var(--card);display:flex;align-items:center;justify-content:center;text-align:center;padding:20px;border-radius:8px;';
                const placeholderTitle = document.createElement('div');
                placeholderTitle.style.color = 'var(--text)';
                placeholderTitle.textContent = movie.title;
                placeholder.appendChild(placeholderTitle);
                card.appendChild(placeholder);
            }
            
            const title = document.createElement('div');
            title.className = 't-title';
            title.textContent = movie.title;
            
            card.appendChild(title);
            
            card.addEventListener('click', async () => {
                const details = await apiCall(`/api/movies/${movie.id}/`);
                if (details.movie) openQuickView(details.movie);
            });
            
            return card;
        };
        
        // Add movies twice for infinite loop effect
        result.trending.forEach(movie => {
            trendingList.appendChild(createCard(movie));
        });
        
        // Duplicate for seamless loop
        result.trending.forEach(movie => {
            trendingList.appendChild(createCard(movie));
        });
    } catch (err) {
        console.error('Failed to load trending', err);
    }
}

// Quick view modal
async function openQuickView(movie) {
    const overlay = document.getElementById('quickViewOverlay');
    const title = document.getElementById('qTitle');
    const meta = document.getElementById('qMeta');
    const desc = document.getElementById('qDesc');
    const poster = document.getElementById('qPoster');
    
    if (!overlay) return;
    
    title.textContent = movie.title + (movie.year ? ` (${movie.year})` : '');
    meta.textContent = `${movie.lang?.toUpperCase() || ''} ${movie.rating ? '· ⭐ ' + movie.rating : ''}`;
    desc.textContent = movie.desc || '';
    
    if (movie.poster) {
        poster.style.backgroundImage = `url('${movie.poster}')`;
    } else {
        poster.style.backgroundImage = '';
    }
    
    overlay.style.display = 'flex';
    
    // For Wikipedia movies, show Wikipedia link prominently
    if (movie.source === 'wikipedia' && movie.wiki_url) {
        const castEl = document.getElementById('qCast');
        const crewEl = document.getElementById('qCrew');
        const extrasEl = document.getElementById('qExtras');
        
        if (castEl) castEl.innerHTML = '<div style="color:var(--muted);font-size:13px">Cast information not available from Wikipedia.</div>';
        if (crewEl) crewEl.innerHTML = '<li style="color:var(--muted)">Crew information not available from Wikipedia.</li>';
        
        if (extrasEl) {
            extrasEl.innerHTML = `
                <div style="margin-top:0;margin-bottom:16px;padding:14px;background:rgba(66,133,244,0.08);border-radius:8px;border-left:4px solid #4285f4">
                    <strong style="display:block;margin-bottom:10px;color:#4285f4;font-size:14px">📖 From Wikipedia</strong>
                    <p style="margin:0 0 10px 0;font-size:13px;line-height:1.6;color:var(--text)">
                        This movie information is sourced from Wikipedia. Click below to view the full article for more details including cast, crew, and production information.
                    </p>
                    <a href="${movie.wiki_url}" target="_blank" rel="noopener noreferrer" 
                       style="color:#4285f4;font-size:12px;text-decoration:none;font-weight:600"
                       onmouseover="this.style.textDecoration='underline'" 
                       onmouseout="this.style.textDecoration='none'">
                        Read full article on Wikipedia →
                    </a>
                </div>
            `;
        }
        
        return;
    }
    
    // Load full details if we have a TMDb ID
    if (movie.id && movie.source !== 'wikipedia') {
        try {
            const result = await apiCall(`/api/movies/${movie.id}/`);
            if (result.movie) {
                // Update with full details
                const fullMovie = result.movie;
                
                console.log('Full movie details:', fullMovie);
                console.log('Wikipedia data:', fullMovie.wikipedia);
                
                // Update cast
                const castEl = document.getElementById('qCast');
                if (castEl && fullMovie.cast && fullMovie.cast.length > 0) {
                    castEl.innerHTML = '';
                    fullMovie.cast.forEach(person => {
                        const item = document.createElement('div');
                        item.className = 'cast-item';
                        
                        const img = document.createElement('img');
                        img.src = person.profile || '';
                        img.alt = person.name;
                        img.loading = 'lazy';
                        
                        const name = document.createElement('span');
                        name.className = 'actor';
                        name.textContent = person.name;
                        
                        const role = document.createElement('span');
                        role.className = 'role';
                        role.textContent = person.character || '';
                        
                        item.appendChild(img);
                        item.appendChild(name);
                        item.appendChild(role);
                        
                        // Add click handler to open person profile
                        if (person.id) {
                            item.style.cursor = 'pointer';
                            item.addEventListener('click', async (e) => {
                                e.stopPropagation();
                                await openPersonProfile(person.id);
                            });
                        }
                        
                        castEl.appendChild(item);
                    });
                }
                
                // Update crew
                const crewEl = document.getElementById('qCrew');
                if (crewEl && fullMovie.crew && fullMovie.crew.length > 0) {
                    crewEl.innerHTML = '';
                    fullMovie.crew.slice(0, 6).forEach(person => {
                        const li = document.createElement('li');
                        li.textContent = `${person.job}: ${person.name}`;
                        crewEl.appendChild(li);
                    });
                }
                
                // Add Wikipedia info if available
                if (fullMovie.wikipedia && fullMovie.wikipedia.extract) {
                    console.log('Adding Wikipedia section...');
                    
                    const extrasEl = document.getElementById('qExtras');
                    if (extrasEl) {
                        // Create Wikipedia container
                        const wikiContainer = document.createElement('div');
                        
                        const wikiSection = document.createElement('div');
                        wikiSection.style.cssText = 'margin-top:0;margin-bottom:16px;padding:14px;background:rgba(255,107,107,0.08);border-radius:8px;border-left:4px solid var(--accent)';
                        
                        const wikiTitle = document.createElement('strong');
                        wikiTitle.innerHTML = '📖 Wikipedia Info';
                        wikiTitle.style.cssText = 'display:block;margin-bottom:10px;color:var(--accent);font-size:14px';
                        
                        const wikiText = document.createElement('p');
                        wikiText.textContent = fullMovie.wikipedia.extract;
                        wikiText.style.cssText = 'margin:0 0 10px 0;font-size:13px;line-height:1.6;color:var(--text)';
                        
                        if (fullMovie.wikipedia.url) {
                            const wikiLink = document.createElement('a');
                            wikiLink.href = fullMovie.wikipedia.url;
                            wikiLink.target = '_blank';
                            wikiLink.rel = 'noopener noreferrer';
                            wikiLink.textContent = 'Read more on Wikipedia →';
                            wikiLink.style.cssText = 'color:var(--accent);font-size:12px;text-decoration:none;font-weight:600';
                            wikiLink.onmouseover = function() { this.style.textDecoration = 'underline'; };
                            wikiLink.onmouseout = function() { this.style.textDecoration = 'none'; };
                            
                            wikiSection.appendChild(wikiTitle);
                            wikiSection.appendChild(wikiText);
                            wikiSection.appendChild(wikiLink);
                        } else {
                            wikiSection.appendChild(wikiTitle);
                            wikiSection.appendChild(wikiText);
                        }
                        
                        wikiContainer.appendChild(wikiSection);
                        
                        // Insert at the beginning of extras
                        const firstChild = extrasEl.firstElementChild;
                        if (firstChild) {
                            extrasEl.insertBefore(wikiContainer, firstChild);
                        } else {
                            extrasEl.appendChild(wikiContainer);
                        }
                        
                        console.log('Wikipedia section added successfully');
                    } else {
                        console.error('qExtras element not found!');
                    }
                } else {
                    console.log('No Wikipedia data available:', fullMovie.wikipedia);
                }
                
                // Update similar movies
                const similarEl = document.getElementById('qSimilar');
                if (similarEl && fullMovie.similar && fullMovie.similar.length > 0) {
                    similarEl.innerHTML = '';
                    fullMovie.similar.forEach(m => {
                        const card = document.createElement('div');
                        card.className = 'similar-movie-card';
                        
                        const img = document.createElement('img');
                        img.src = m.poster || '';
                        img.alt = m.title;
                        img.loading = 'lazy';
                        
                        const title = document.createElement('span');
                        title.className = 'movie-title';
                        title.textContent = m.title;
                        
                        const year = document.createElement('span');
                        year.className = 'movie-year';
                        year.textContent = m.year || '';
                        
                        card.appendChild(img);
                        card.appendChild(title);
                        card.appendChild(year);
                        
                        card.addEventListener('click', async () => {
                            const details = await apiCall(`/api/movies/${m.id}/`);
                            if (details.movie) openQuickView(details.movie);
                        });
                        
                        similarEl.appendChild(card);
                    });
                }
                
                // Update videos
                const videosEl = document.getElementById('qVideos');
                if (videosEl && fullMovie.videos && fullMovie.videos.length > 0) {
                    videosEl.innerHTML = '';
                    fullMovie.videos.slice(0, 6).forEach(v => {
                        const div = document.createElement('div');
                        div.className = 'media-item video-thumb';
                        
                        const img = document.createElement('img');
                        img.src = `https://img.youtube.com/vi/${v.key}/hqdefault.jpg`;
                        img.alt = v.name || v.type;
                        img.loading = 'lazy';
                        
                        const label = document.createElement('div');
                        label.className = 'label';
                        label.textContent = v.type || v.name || 'Video';
                        
                        div.appendChild(img);
                        div.appendChild(label);
                        
                        div.addEventListener('click', () => {
                            window.open(`https://www.youtube.com/watch?v=${v.key}`, '_blank');
                        });
                        
                        videosEl.appendChild(div);
                    });
                }
            }
        } catch (err) {
            console.error('Failed to load movie details', err);
        }
    }
    
    // Setup close button
    document.getElementById('qClose').onclick = closeQuickView;
}

function closeQuickView() {
    const overlay = document.getElementById('quickViewOverlay');
    if (overlay) overlay.style.display = 'none';
}

// Person profile modal functions
async function openPersonProfile(personId) {
    try {
        console.log('Opening person profile:', personId);
        const overlay = document.getElementById('personOverlay');
        const nameEl = document.getElementById('pName');
        const pic = document.getElementById('pPic');
        const meta = document.getElementById('pMeta');
        const bio = document.getElementById('pBio');
        const knownEl = document.getElementById('pKnown');
        
        if (!overlay || !nameEl) return;
        
        // Show loading state
        nameEl.innerHTML = '<div class="movie-loader" style="font-size:18px">LOADING<span class="loading-dots"><span>.</span><span>.</span><span>.</span></span></div>';
        if (meta) meta.textContent = '';
        if (bio) bio.innerHTML = '<div class="loading-container" style="padding:20px"><div class="movie-loader" style="font-size:16px">LOADING<span class="loading-dots"><span>.</span><span>.</span><span>.</span></span></div></div>';
        if (knownEl) knownEl.innerHTML = '<div class="loading-container" style="padding:20px"><div class="movie-loader" style="font-size:16px">LOADING<span class="loading-dots"><span>.</span><span>.</span><span>.</span></span></div></div>';
        overlay.style.display = 'flex';
        
        // Fetch person details
        const result = await apiCall(`/api/person/${personId}/`);
        
        if (result.error) {
            showError(result.error);
            closePersonProfile();
            return;
        }
        
        const person = result.person;
        
        console.log('Person details:', person);
        console.log('Wikipedia data:', person.wikipedia);
        
        // Update UI with person details
        nameEl.textContent = person.name || 'Unknown';
        
        if (pic) {
            if (person.profile_path) {
                pic.src = person.profile_path;
                pic.alt = person.name || 'Profile';
            } else {
                pic.src = '';
                pic.alt = 'No image';
            }
        }
        
        // Meta information
        const parts = [];
        if (person.birthday) parts.push(`Born: ${person.birthday}`);
        if (person.place_of_birth) parts.push(person.place_of_birth);
        if (meta) meta.textContent = parts.join(' · ');
        
        // Biography (prefer Wikipedia, fallback to TMDb)
        let bioText = '';
        if (person.wikipedia && person.wikipedia.extract) {
            console.log('Using Wikipedia bio');
            bioText = person.wikipedia.extract;
            
            if (bio) {
                bio.innerHTML = '';
                bio.style.position = 'relative';
                
                // Add Wikipedia badge
                const wikiBadge = document.createElement('div');
                wikiBadge.innerHTML = '📖 From Wikipedia';
                wikiBadge.style.cssText = 'display:inline-block;background:rgba(255,107,107,0.2);color:var(--accent);padding:5px 10px;border-radius:5px;font-size:11px;margin-bottom:10px;font-weight:700;letter-spacing:0.5px';
                bio.appendChild(wikiBadge);
                
                const bioContent = document.createElement('div');
                bioContent.textContent = bioText;
                bioContent.style.cssText = 'margin-top:8px';
                bio.appendChild(bioContent);
                
                // Add Wikipedia link
                if (person.wikipedia.url) {
                    const wikiLink = document.createElement('a');
                    wikiLink.href = person.wikipedia.url;
                    wikiLink.target = '_blank';
                    wikiLink.rel = 'noopener noreferrer';
                    wikiLink.textContent = '→ Read full Wikipedia article';
                    wikiLink.style.cssText = 'display:inline-block;margin-top:12px;color:var(--accent);text-decoration:none;font-size:12px;font-weight:600;padding:6px 12px;border:1px solid var(--accent);border-radius:4px';
                    wikiLink.onmouseover = function() { this.style.background = 'rgba(255,107,107,0.1)'; };
                    wikiLink.onmouseout = function() { this.style.background = 'transparent'; };
                    bio.appendChild(wikiLink);
                }
            }
        } else {
            console.log('Using TMDb bio');
            bioText = person.biography || 'Biography not available.';
            if (bio) {
                bio.textContent = bioText;
            }
        }
        
        // Known for movies
        if (knownEl && person.known_for && person.known_for.length > 0) {
            knownEl.innerHTML = '';
            person.known_for.forEach(movie => {
                const item = document.createElement('div');
                item.className = 'known-item';
                
                const img = document.createElement('img');
                img.src = movie.poster || '';
                img.alt = movie.title || 'Movie';
                img.loading = 'lazy';
                
                const title = document.createElement('div');
                title.className = 'label';
                title.textContent = movie.title || '';
                
                item.appendChild(img);
                item.appendChild(title);
                
                // Make clickable to show movie details
                if (movie.id) {
                    item.style.cursor = 'pointer';
                    item.addEventListener('click', async () => {
                        const movieDetails = await apiCall(`/api/movies/${movie.id}/`);
                        if (movieDetails.movie) {
                            closePersonProfile();
                            openQuickView(movieDetails.movie);
                        }
                    });
                }
                
                knownEl.appendChild(item);
            });
        } else if (knownEl) {
            knownEl.innerHTML = '<div style="color:var(--muted)">Not available.</div>';
        }
        
    } catch (err) {
        console.error('openPersonProfile error:', err);
        showError('Unable to load profile: ' + err.message);
        closePersonProfile();
    }
}

function closePersonProfile() {
    const overlay = document.getElementById('personOverlay');
    if (overlay) overlay.style.display = 'none';
}

// Wire up person modal close button
document.getElementById('pClose')?.addEventListener('click', (e) => {
    e.preventDefault();
    closePersonProfile();
});

// Event listeners
if (recommendBtn) {
    recommendBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Recommend button clicked');
        discoverMovies();
    });
} else {
    console.error('Recommend button not found!');
}

if (searchBtn) {
    searchBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Search button clicked');
        discoverMovies();
    });
}

// Voice Search functionality
if (voiceSearchBtn) {
    // Check if browser supports Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        let isRecording = false;
        
        voiceSearchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (isRecording) {
                recognition.stop();
                return;
            }
            
            try {
                recognition.start();
                isRecording = true;
                voiceSearchBtn.classList.add('recording');
                console.log('Voice recognition started');
                showError('🎤 Listening... Speak now!');
            } catch (error) {
                console.error('Speech recognition error:', error);
                showError('Failed to start voice recognition. Please try again.');
            }
        });
        
        recognition.addEventListener('result', (e) => {
            const transcript = e.results[0][0].transcript;
            console.log('Voice input received:', transcript);
            searchEl.value = transcript;
            clearError();
            // Automatically trigger search after voice input
            discoverMovies();
        });
        
        recognition.addEventListener('end', () => {
            isRecording = false;
            voiceSearchBtn.classList.remove('recording');
            console.log('Voice recognition ended');
        });
        
        recognition.addEventListener('error', (e) => {
            console.error('Speech recognition error:', e.error);
            isRecording = false;
            voiceSearchBtn.classList.remove('recording');
            
            let errorMessage = 'Voice search error. ';
            switch(e.error) {
                case 'no-speech':
                    errorMessage += 'No speech detected. Please try again.';
                    break;
                case 'audio-capture':
                    errorMessage += 'Microphone not found. Please check your device.';
                    break;
                case 'not-allowed':
                    errorMessage += 'Microphone access denied. Please enable it in your browser settings.';
                    break;
                default:
                    errorMessage += 'Please try again.';
            }
            showError(errorMessage);
        });
        
    } else {
        // Browser doesn't support Web Speech API
        voiceSearchBtn.style.display = 'none';
        console.warn('Web Speech API not supported in this browser');
    }
}

surpriseBtn?.addEventListener('click', () => {
    // Reset to random selections
    const genres = ['Any', 'Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Thriller', 'Sci-Fi', 'Crime', 'Animation', 'Fantasy'];
    const languages = ['Any', 'English', 'Hindi', 'Malayalam', 'Tamil', 'Korean'];
    
    genreEl.value = genres[Math.floor(Math.random() * genres.length)];
    langEl.value = languages[Math.floor(Math.random() * languages.length)];
    countEl.value = Math.floor(Math.random() * 15) + 10; // 10-25 movies
    
    // Random timeframe
    const timeframes = document.querySelectorAll('input[name="timeframe"]');
    if (timeframes.length > 0) {
        const randomTimeframe = timeframes[Math.floor(Math.random() * timeframes.length)];
        randomTimeframe.checked = true;
    }
    
    discoverMovies();
});

// Add Enter key listener to search box
if (searchEl) {
    searchEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            console.log('Enter pressed in search box');
            discoverMovies();
        }
    });
}

trendingBtn?.addEventListener('click', async () => {
    try {
        const result = await apiCall('/api/movies/trending/');
        if (result.trending) {
            renderResults(result.trending);
        }
    } catch (err) {
        showError('Failed to load trending movies');
    }
});

favoritesBtn?.addEventListener('click', async () => {
    if (!window.IS_AUTHENTICATED) {
        openSignInModal();
        return;
    }
    try {
        const result = await apiCall('/api/favorites/');
        if (result.favorites) {
            renderResults(result.favorites);
        } else {
            showError('No favorites yet');
        }
    } catch (err) {
        showError('Failed to load favorites');
    }
});

watchLaterBtn?.addEventListener('click', async () => {
    if (!window.IS_AUTHENTICATED) {
        openSignInModal();
        return;
    }
    try {
        const result = await apiCall('/api/watch-later/');
        if (result.watch_later) {
            renderResults(result.watch_later);
        } else {
            showError('Watch later list is empty');
        }
    } catch (err) {
        showError('Failed to load watch later list');
    }
});

libraryBtn?.addEventListener('click', async () => {
    if (!window.IS_AUTHENTICATED) {
        openSignInModal();
        return;
    }
    try {
        const result = await apiCall('/api/library/');
        if (result.library) {
            renderResults(result.library);
        } else {
            showError('Library is empty');
        }
    } catch (err) {
        showError('Failed to load library');
    }
});

// Load trending on page load
loadTrending();

// New UI Element Handlers
const showAdvancedBtn = document.getElementById('showAdvancedBtn');
const closeAdvancedBtn = document.getElementById('closeAdvancedBtn');
const advancedFilters = document.getElementById('advancedFilters');
const surpriseMeBtn = document.getElementById('surpriseBtn');
const resetFiltersBtn = document.getElementById('resetFilters');
const filterChips = document.querySelectorAll('.filter-chip[data-genre]');

// Show/Hide Advanced Filters
showAdvancedBtn?.addEventListener('click', () => {
    advancedFilters.style.display = 'block';
    showAdvancedBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});

closeAdvancedBtn?.addEventListener('click', () => {
    advancedFilters.style.display = 'none';
});

// Quick Genre Filter Chips
filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const genre = chip.getAttribute('data-genre');
        genreEl.value = genre;
        if (advancedFilters.style.display !== 'block') {
            advancedFilters.style.display = 'block';
        }
        // Scroll to filters
        advancedFilters.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
});

// Surprise Me Button (redirects to hidden surprise button)
surpriseMeBtn?.addEventListener('click', () => {
    const hiddenSurprise = document.getElementById('surprise');
    if (hiddenSurprise) {
        hiddenSurprise.click();
    }
});

// Reset Filters
resetFiltersBtn?.addEventListener('click', () => {
    genreEl.value = 'Any';
    langEl.value = 'Any';
    certEl.value = 'Any';
    sortEl.value = 'none';
    countEl.value = '20';
    searchEl.value = '';
    const anyTimeframe = document.querySelector('input[name="timeframe"][value="any"]');
    if (anyTimeframe) anyTimeframe.checked = true;
    showError('Filters reset');
    setTimeout(() => clearError(), 2000);
});

// Update user label display
if (window.IS_AUTHENTICATED && window.USERNAME) {
    const userLabel = document.getElementById('userLabel');
    if (userLabel) {
        userLabel.textContent = window.USERNAME;
    }
    const signInBtn = document.getElementById('signInBtn');
    if (signInBtn) {
        signInBtn.style.background = 'transparent';
        signInBtn.style.border = '1px solid var(--border)';
    }
}

console.log('✅ Movie Recommender loaded successfully!');
console.log('🎬 New UI features initialized');
