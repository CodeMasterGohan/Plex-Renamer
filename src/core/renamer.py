"""
Media renaming engine that applies Plex naming conventions.
"""

import os
import re
import shutil
from typing import Dict, List, Optional, Tuple
from src.core.file_parser import MediaFileInfo
from src.api.tmdb import TMDBClient
from src.api.tvdb import TVDBClient
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RenameOperation:
    """Represents a single file rename operation."""
    
    def __init__(self, source_path: str, target_path: str, operation_type: str = "rename"):
        self.source_path = source_path
        self.target_path = target_path
        self.operation_type = operation_type  # "rename", "move", "copy"
        self.success = False
        self.error_message = None
        self.metadata = {}  # Store metadata used for the operation

class MediaRenamer:
    """Main renaming engine for media files."""
    
    def __init__(self, config: Config):
        """
        Initialize the media renamer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize API clients
        self.tmdb_client = None
        self.tvdb_client = None
        
        if config.tmdb_api_key:
            self.tmdb_client = TMDBClient(
                config.tmdb_api_key,
                config.get('API', 'preferred_language', 'en-US')
            )
        
        if config.tvdb_api_key:
            self.tvdb_client = TVDBClient(config.tvdb_api_key)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim whitespace
        filename = filename.strip()
        
        # Remove trailing periods (not allowed on Windows)
        filename = filename.rstrip('.')
        
        return filename
    
    def generate_movie_name(self, media_info: MediaFileInfo, metadata: Dict = None) -> str:
        """
        Generate Plex-compliant movie filename.
        
        Args:
            media_info: Parsed media file information
            metadata: Optional metadata from API
            
        Returns:
            New filename (without extension)
        """
        if metadata:
            title = metadata.get('title', media_info.title)
            release_date = metadata.get('release_date', '')
            if release_date:
                year = release_date[:4]
            else:
                year = str(media_info.year) if media_info.year else ''
        else:
            title = media_info.title
            year = str(media_info.year) if media_info.year else ''
        
        # Format: "Movie Title (Year)"
        if year:
            new_name = f"{title} ({year})"
        else:
            new_name = title
        
        return self.sanitize_filename(new_name)
    
    def generate_tv_episode_name(self, media_info: MediaFileInfo, show_metadata: Dict = None, 
                                episode_metadata: Dict = None) -> str:
        """
        Generate Plex-compliant TV episode filename.
        
        Args:
            media_info: Parsed media file information
            show_metadata: Optional show metadata from API
            episode_metadata: Optional episode metadata from API
            
        Returns:
            New filename (without extension)
        """
        if show_metadata:
            show_title = show_metadata.get('name', show_metadata.get('title', media_info.title))
        else:
            show_title = media_info.title
        
        season = media_info.season or 1
        episode = media_info.episode or 1
        
        # Format: "Show Name - sXXeYY - Episode Title"
        episode_part = f"s{season:02d}e{episode:02d}"
        
        # Handle multi-episode files
        if media_info.episode_end:
            episode_part += f"-e{media_info.episode_end:02d}"
        
        new_name = f"{show_title} - {episode_part}"
        
        # Add episode title if available and configured
        if (episode_metadata and 
            self.config.get_boolean('TV_SHOWS', 'include_episode_title', True)):
            episode_title = episode_metadata.get('name', episode_metadata.get('title'))
            if episode_title:
                new_name += f" - {episode_title}"
        
        return self.sanitize_filename(new_name)
    
    def generate_tv_show_folder_name(self, show_metadata: Dict, media_info: MediaFileInfo) -> str:
        """
        Generate Plex-compliant TV show folder name.
        
        Args:
            show_metadata: Show metadata from API
            media_info: Parsed media file information
            
        Returns:
            Folder name
        """
        show_title = show_metadata.get('name', show_metadata.get('title', media_info.title))
        
        # Get year from first air date
        first_air_date = show_metadata.get('first_air_date', show_metadata.get('first_air_time', ''))
        if first_air_date:
            year = first_air_date[:4]
        else:
            year = str(media_info.year) if media_info.year else ''
        
        # Format: "Show Name (Year)"
        if year:
            folder_name = f"{show_title} ({year})"
        else:
            folder_name = show_title
        
        # Add series ID if configured
        if self.config.get_boolean('TV_SHOWS', 'include_series_id', False):
            preferred_source = self.config.get('TV_SHOWS', 'preferred_id_source', 'tvdb')
            if preferred_source == 'tmdb' and 'id' in show_metadata:
                folder_name += f" {{tmdb-{show_metadata['id']}}}"
            elif preferred_source == 'tvdb' and 'tvdb_id' in show_metadata:
                folder_name += f" {{tvdb-{show_metadata['tvdb_id']}}}"
        
        return self.sanitize_filename(folder_name)
    
    def get_movie_metadata(self, media_info: MediaFileInfo) -> Optional[Dict]:
        """
        Get movie metadata from TMDB.
        
        Args:
            media_info: Parsed media file information
            
        Returns:
            Movie metadata or None
        """
        if not self.tmdb_client:
            self.logger.warning("TMDB client not available")
            return None
        
        try:
            movie = self.tmdb_client.find_best_movie_match(media_info.title, media_info.year)
            if movie:
                # Get detailed information
                details = self.tmdb_client.get_movie_details(movie['id'])
                return details if details else movie
            return None
        except Exception as e:
            self.logger.error(f"Error fetching movie metadata for {media_info.title}: {e}")
            return None
    
    def get_tv_show_metadata(self, media_info: MediaFileInfo) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Get TV show and episode metadata.
        
        Args:
            media_info: Parsed media file information
            
        Returns:
            Tuple of (show_metadata, episode_metadata)
        """
        show_metadata = None
        episode_metadata = None
        
        # Try TVDB first (preferred for TV shows)
        if self.tvdb_client:
            try:
                series = self.tvdb_client.find_best_series_match(media_info.title, media_info.year)
                if series:
                    show_metadata = self.tvdb_client.get_series_details(series['tvdb_id'])
                    if show_metadata and media_info.season and media_info.episode:
                        episode = self.tvdb_client.find_episode_by_season_episode(
                            series['tvdb_id'], media_info.season, media_info.episode
                        )
                        if episode:
                            episode_metadata = self.tvdb_client.get_episode_details(episode['id'])
            except Exception as e:
                self.logger.error(f"Error fetching TVDB metadata for {media_info.title}: {e}")
        
        # Fallback to TMDB if TVDB failed or not available
        if not show_metadata and self.tmdb_client:
            try:
                show = self.tmdb_client.find_best_tv_match(media_info.title, media_info.year)
                if show:
                    show_metadata = self.tmdb_client.get_tv_details(show['id'])
                    if show_metadata and media_info.season and media_info.episode:
                        episode_metadata = self.tmdb_client.get_tv_episode_details(
                            show['id'], media_info.season, media_info.episode
                        )
            except Exception as e:
                self.logger.error(f"Error fetching TMDB metadata for {media_info.title}: {e}")
        
        return show_metadata, episode_metadata
    
    def plan_movie_rename(self, media_info: MediaFileInfo) -> RenameOperation:
        """
        Plan a movie rename operation.
        
        Args:
            media_info: Parsed media file information
            
        Returns:
            RenameOperation object
        """
        # Get metadata
        metadata = self.get_movie_metadata(media_info)
        
        # Generate new filename
        new_name = self.generate_movie_name(media_info, metadata)
        new_filename = new_name + media_info.extension
        
        # Determine target path
        movies_path = self.config.movies_path
        
        if self.config.get_boolean('MOVIES', 'create_movie_folders', True):
            # Create individual movie folder
            target_dir = os.path.join(movies_path, new_name)
            target_path = os.path.join(target_dir, new_filename)
        else:
            # Place directly in movies folder
            target_path = os.path.join(movies_path, new_filename)
        
        operation = RenameOperation(media_info.file_path, target_path)
        operation.metadata = metadata
        
        return operation
    
    def plan_tv_rename(self, media_info: MediaFileInfo) -> RenameOperation:
        """
        Plan a TV show rename operation.
        
        Args:
            media_info: Parsed media file information
            
        Returns:
            RenameOperation object
        """
        # Get metadata
        show_metadata, episode_metadata = self.get_tv_show_metadata(media_info)
        
        # Generate folder and file names
        if show_metadata:
            show_folder = self.generate_tv_show_folder_name(show_metadata, media_info)
        else:
            show_folder = self.sanitize_filename(media_info.title)
        
        episode_name = self.generate_tv_episode_name(media_info, show_metadata, episode_metadata)
        new_filename = episode_name + media_info.extension
        
        # Determine target path
        tv_shows_path = self.config.tv_shows_path
        season = media_info.season or 1
        season_folder = f"Season {season:02d}"
        
        target_path = os.path.join(tv_shows_path, show_folder, season_folder, new_filename)
        
        operation = RenameOperation(media_info.file_path, target_path)
        operation.metadata = {
            'show': show_metadata,
            'episode': episode_metadata
        }
        
        return operation
    
    def execute_operation(self, operation: RenameOperation, dry_run: bool = True) -> bool:
        """
        Execute a rename operation.
        
        Args:
            operation: RenameOperation to execute
            dry_run: If True, don't actually perform the operation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                self.logger.info(f"DRY RUN: Would rename {operation.source_path} -> {operation.target_path}")
                operation.success = True
                return True
            
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(operation.target_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                self.logger.info(f"Created directory: {target_dir}")
            
            # Check if target already exists
            if os.path.exists(operation.target_path):
                self.logger.warning(f"Target file already exists: {operation.target_path}")
                operation.error_message = "Target file already exists"
                return False
            
            # Perform the operation
            if operation.operation_type == "move":
                shutil.move(operation.source_path, operation.target_path)
            elif operation.operation_type == "copy":
                shutil.copy2(operation.source_path, operation.target_path)
            else:  # rename (default)
                os.rename(operation.source_path, operation.target_path)
            
            self.logger.info(f"Renamed: {operation.source_path} -> {operation.target_path}")
            operation.success = True
            return True
            
        except Exception as e:
            error_msg = f"Error executing operation: {e}"
            self.logger.error(error_msg)
            operation.error_message = error_msg
            operation.success = False
            return False
    
    def plan_operations(self, media_files: List[MediaFileInfo]) -> List[RenameOperation]:
        """
        Plan rename operations for a list of media files.
        
        Args:
            media_files: List of MediaFileInfo objects
            
        Returns:
            List of RenameOperation objects
        """
        operations = []
        
        for media_info in media_files:
            try:
                if media_info.media_type == 'movie':
                    operation = self.plan_movie_rename(media_info)
                elif media_info.media_type == 'tv':
                    operation = self.plan_tv_rename(media_info)
                else:
                    self.logger.warning(f"Unknown media type for {media_info.file_path}")
                    continue
                
                operations.append(operation)
                
            except Exception as e:
                self.logger.error(f"Error planning operation for {media_info.file_path}: {e}")
        
        return operations
    
    def execute_operations(self, operations: List[RenameOperation], 
                          dry_run: bool = True) -> Dict[str, int]:
        """
        Execute a list of rename operations.
        
        Args:
            operations: List of RenameOperation objects
            dry_run: If True, don't actually perform the operations
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for operation in operations:
            if self.execute_operation(operation, dry_run):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        self.logger.info(f"Operation results: {results}")
        return results 