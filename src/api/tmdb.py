"""
TMDB (The Movie Database) API integration.
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TMDBClient:
    """Client for interacting with The Movie Database API."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str, language: str = "en-US"):
        """
        Initialize TMDB client.
        
        Args:
            api_key: TMDB API key
            language: Preferred language for results
        """
        self.api_key = api_key
        self.language = language
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 0.25  # 4 requests per second max
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make an API request to TMDB.
        
        Args:
            endpoint: API endpoint to call
            params: Additional parameters
            
        Returns:
            JSON response or None if failed
        """
        self._wait_for_rate_limit()
        
        if params is None:
            params = {}
        
        params.update({
            'api_key': self.api_key,
            'language': self.language
        })
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("TMDB API: Invalid API key")
                return None
            elif response.status_code == 429:
                logger.warning("TMDB API: Rate limit exceeded, waiting...")
                time.sleep(5)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"TMDB API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TMDB API request failed: {e}")
            return None
    
    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """
        Search for movies by title.
        
        Args:
            title: Movie title to search for
            year: Optional release year to filter results
            
        Returns:
            List of movie results
        """
        params = {'query': title}
        if year:
            params['year'] = year
        
        response = self._make_request('search/movie', params)
        if response and 'results' in response:
            return response['results']
        return []
    
    def search_tv(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """
        Search for TV shows by title.
        
        Args:
            title: TV show title to search for
            year: Optional first air date year to filter results
            
        Returns:
            List of TV show results
        """
        params = {'query': title}
        if year:
            params['first_air_date_year'] = year
        
        response = self._make_request('search/tv', params)
        if response and 'results' in response:
            return response['results']
        return []
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Get detailed information about a movie.
        
        Args:
            movie_id: TMDB movie ID
            
        Returns:
            Movie details or None if not found
        """
        return self._make_request(f'movie/{movie_id}')
    
    def get_tv_details(self, tv_id: int) -> Optional[Dict]:
        """
        Get detailed information about a TV show.
        
        Args:
            tv_id: TMDB TV show ID
            
        Returns:
            TV show details or None if not found
        """
        return self._make_request(f'tv/{tv_id}')
    
    def get_tv_season_details(self, tv_id: int, season_number: int) -> Optional[Dict]:
        """
        Get detailed information about a TV season.
        
        Args:
            tv_id: TMDB TV show ID
            season_number: Season number
            
        Returns:
            Season details or None if not found
        """
        return self._make_request(f'tv/{tv_id}/season/{season_number}')
    
    def get_tv_episode_details(self, tv_id: int, season_number: int, episode_number: int) -> Optional[Dict]:
        """
        Get detailed information about a TV episode.
        
        Args:
            tv_id: TMDB TV show ID
            season_number: Season number
            episode_number: Episode number
            
        Returns:
            Episode details or None if not found
        """
        return self._make_request(f'tv/{tv_id}/season/{season_number}/episode/{episode_number}')
    
    def find_best_movie_match(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Find the best matching movie for a given title and year.
        
        Args:
            title: Movie title
            year: Optional release year
            
        Returns:
            Best matching movie or None
        """
        results = self.search_movie(title, year)
        if not results:
            return None
        
        # If we have a year, prefer exact matches
        if year:
            for movie in results:
                release_date = movie.get('release_date', '')
                if release_date and release_date.startswith(str(year)):
                    return movie
        
        # Return the first result (highest popularity)
        return results[0]
    
    def find_best_tv_match(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Find the best matching TV show for a given title and year.
        
        Args:
            title: TV show title
            year: Optional first air date year
            
        Returns:
            Best matching TV show or None
        """
        results = self.search_tv(title, year)
        if not results:
            return None
        
        # If we have a year, prefer exact matches
        if year:
            for show in results:
                first_air_date = show.get('first_air_date', '')
                if first_air_date and first_air_date.startswith(str(year)):
                    return show
        
        # Return the first result (highest popularity)
        return results[0] 