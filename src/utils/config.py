"""
Configuration management for the Plex Media Renamer application.
"""

import configparser
import os
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_file="config.ini"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default configuration."""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.create_default_config()
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration."""
        logger.info("Creating default configuration")
        
        # API Settings
        self.config['API'] = {
            'tmdb_api_key': '',
            'tvdb_api_key': '',
            'preferred_language': 'en-US'
        }
        
        # Paths
        self.config['PATHS'] = {
            'base_media_path': '',
            'movies_subfolder': 'movies',
            'tv_shows_subfolder': 'tv_shows'
        }
        
        # Movie Settings
        self.config['MOVIES'] = {
            'create_movie_folders': 'true',
            'include_year_in_folder': 'true'
        }
        
        # TV Show Settings
        self.config['TV_SHOWS'] = {
            'include_episode_title': 'true',
            'include_series_id': 'false',
            'preferred_id_source': 'tvdb'  # tvdb or tmdb
        }
        
        # General Settings
        self.config['GENERAL'] = {
            'dry_run_mode': 'true',
            'log_level': 'INFO',
            'backup_original_names': 'true'
        }
        
        self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, section, key, fallback=None):
        """Get a configuration value."""
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section, key, value):
        """Set a configuration value."""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))
    
    def get_boolean(self, section, key, fallback=False):
        """Get a boolean configuration value."""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def set_boolean(self, section, key, value):
        """Set a boolean configuration value."""
        self.set(section, key, 'true' if value else 'false')
    
    # Convenience methods for common settings
    @property
    def tmdb_api_key(self):
        return self.get('API', 'tmdb_api_key')
    
    @tmdb_api_key.setter
    def tmdb_api_key(self, value):
        self.set('API', 'tmdb_api_key', value)
    
    @property
    def tvdb_api_key(self):
        return self.get('API', 'tvdb_api_key')
    
    @tvdb_api_key.setter
    def tvdb_api_key(self, value):
        self.set('API', 'tvdb_api_key', value)
    
    @property
    def base_media_path(self):
        return self.get('PATHS', 'base_media_path')
    
    @base_media_path.setter
    def base_media_path(self, value):
        self.set('PATHS', 'base_media_path', value)
    
    @property
    def movies_path(self):
        base = self.base_media_path
        subfolder = self.get('PATHS', 'movies_subfolder', 'movies')
        return os.path.join(base, subfolder) if base else ''
    
    @property
    def tv_shows_path(self):
        base = self.base_media_path
        subfolder = self.get('PATHS', 'tv_shows_subfolder', 'tv_shows')
        return os.path.join(base, subfolder) if base else ''
    
    @property
    def dry_run_mode(self):
        return self.get_boolean('GENERAL', 'dry_run_mode', True)
    
    @dry_run_mode.setter
    def dry_run_mode(self, value):
        self.set_boolean('GENERAL', 'dry_run_mode', value) 