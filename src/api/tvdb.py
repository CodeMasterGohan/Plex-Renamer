"""
TVDB (The Television Database) API integration.
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TVDBClient:
    """Client for interacting with The TVDB API v4."""
    
    BASE_URL = "https://api4.thetvdb.com/v4"
    
    def __init__(self, api_key: str):
        """
        Initialize TVDB client.
        
        Args:
            api_key: TVDB API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.token = None
        self.token_expires = 0
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # Conservative rate limiting
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
    
    def _authenticate(self) -> bool:
        """
        Authenticate with TVDB API and get access token.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.BASE_URL}/login",
                json={"apikey": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('token')
                self.token_expires = time.time() + 2592000  # 30 days
                logger.info("TVDB authentication successful")
                return True
            else:
                logger.error(f"TVDB authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"TVDB authentication error: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid authentication token.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.token or time.time() >= self.token_expires:
            return self._authenticate()
        return True
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make an API request to TVDB.
        
        Args:
            endpoint: API endpoint to call
            params: Additional parameters
            
        Returns:
            JSON response or None if failed
        """
        if not self._ensure_authenticated():
            return None
        
        self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.warning("TVDB token expired, re-authenticating...")
                self.token = None
                if self._ensure_authenticated():
                    headers = {"Authorization": f"Bearer {self.token}"}
                    response = self.session.get(url, headers=headers, params=params, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                return None
            elif response.status_code == 429:
                logger.warning("TVDB API: Rate limit exceeded, waiting...")
                time.sleep(5)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"TVDB API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TVDB API request failed: {e}")
            return None
    
    def search_series(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """
        Search for TV series by title.
        
        Args:
            title: Series title to search for
            year: Optional year to filter results
            
        Returns:
            List of series results
        """
        params = {"query": title}
        if year:
            params["year"] = year
        
        response = self._make_request("search", params)
        if response and 'data' in response:
            # Filter for series only (type: series)
            series_results = [item for item in response['data'] if item.get('type') == 'series']
            return series_results
        return []
    
    def get_series_details(self, series_id: int) -> Optional[Dict]:
        """
        Get detailed information about a series.
        
        Args:
            series_id: TVDB series ID
            
        Returns:
            Series details or None if not found
        """
        response = self._make_request(f"series/{series_id}/extended")
        if response and 'data' in response:
            return response['data']
        return None
    
    def get_series_episodes(self, series_id: int, season_number: Optional[int] = None) -> List[Dict]:
        """
        Get episodes for a series.
        
        Args:
            series_id: TVDB series ID
            season_number: Optional season number to filter
            
        Returns:
            List of episodes
        """
        params = {}
        if season_number is not None:
            params['season'] = season_number
        
        response = self._make_request(f"series/{series_id}/episodes/default", params)
        if response and 'data' in response and 'episodes' in response['data']:
            return response['data']['episodes']
        return []
    
    def get_episode_details(self, episode_id: int) -> Optional[Dict]:
        """
        Get detailed information about an episode.
        
        Args:
            episode_id: TVDB episode ID
            
        Returns:
            Episode details or None if not found
        """
        response = self._make_request(f"episodes/{episode_id}/extended")
        if response and 'data' in response:
            return response['data']
        return None
    
    def find_best_series_match(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Find the best matching series for a given title and year.
        
        Args:
            title: Series title
            year: Optional year
            
        Returns:
            Best matching series or None
        """
        results = self.search_series(title, year)
        if not results:
            return None
        
        # If we have a year, prefer exact matches
        if year:
            for series in results:
                first_air_time = series.get('first_air_time', '')
                if first_air_time and str(year) in first_air_time:
                    return series
        
        # Return the first result
        return results[0]
    
    def find_episode_by_season_episode(self, series_id: int, season: int, episode: int) -> Optional[Dict]:
        """
        Find a specific episode by season and episode number.
        
        Args:
            series_id: TVDB series ID
            season: Season number
            episode: Episode number
            
        Returns:
            Episode details or None if not found
        """
        episodes = self.get_series_episodes(series_id, season)
        for ep in episodes:
            if ep.get('seasonNumber') == season and ep.get('number') == episode:
                return ep
        return None 