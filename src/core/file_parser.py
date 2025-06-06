"""
File parsing utilities to extract metadata from media filenames.
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MediaFolderInfo:
    """Container for media folder information."""
    
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.folder_name = os.path.basename(folder_path)
        self.media_file_count = 0
        self.total_file_count = 0
        self.subdirectory_count = 0
        self.detected_type = None  # 'movies', 'tv_shows', 'mixed', or None
        self.confidence_score = 0.0  # 0.0 to 1.0
        self.sample_files = []  # Sample media files found

class MediaFileInfo:
    """Container for parsed media file information."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.directory = os.path.dirname(file_path)
        self.name, self.extension = os.path.splitext(self.filename)
        self.title = None
        self.year = None
        self.season = None
        self.episode = None
        self.episode_end = None  # For multi-episode files
        self.quality = None
        self.source = None
        self.media_type = None  # 'movie' or 'tv'

class FileParser:
    """Parser for extracting metadata from media filenames."""
    
    # Common video file extensions
    VIDEO_EXTENSIONS = {
        '.mkv', '.avi', '.mp4', '.m4v', '.mov', '.wmv', '.flv', 
        '.webm', '.mpg', '.mpeg', '.3gp', '.ogv', '.ts', '.m2ts'
    }
    
    # Quality patterns
    QUALITY_PATTERNS = [
        r'\b(4K|2160p|1080p|720p|480p|360p|240p)\b',
        r'\b(UHD|HD|SD)\b',
        r'\b(BluRay|Blu-Ray|BRRip|BDRip|DVDRip|WEBRip|HDTV|WEB-DL)\b'
    ]
    
    # Source patterns
    SOURCE_PATTERNS = [
        r'\b(BluRay|Blu-Ray|BRRip|BDRip|DVDRip|WEBRip|HDTV|WEB-DL|CAM|TS|TC|SCR|R5|DVDScr)\b'
    ]
    
    # TV show patterns
    TV_PATTERNS = [
        # Standard patterns: S01E01, s1e1, 1x01, etc.
        r'[Ss](\d{1,2})[Ee](\d{1,2})(?:-?[Ee](\d{1,2}))?',  # S01E01 or S01E01-E02
        r'(\d{1,2})x(\d{1,2})(?:-(\d{1,2}))?',  # 1x01 or 1x01-02
        r'Season\s*(\d{1,2}).*Episode\s*(\d{1,2})',  # Season 1 Episode 1
        # Episode only patterns (when in season folder)
        r'^[Ee](\d{1,2})(?:-[Ee](\d{1,2}))?',  # E01 or E01-E02
        r'^(\d{1,2})(?:-(\d{1,2}))?[^x]',  # 01 or 01-02 (not followed by x)
    ]
    
    # Year patterns
    YEAR_PATTERN = r'\b(19\d{2}|20\d{2})\b'
    
    # Folders to ignore when scanning for media
    IGNORE_FOLDERS = {
        '.@__thumb', '@eaDir', '.DS_Store', 'Thumbs.db', '.recycle',
        '.trash', 'lost+found', '.git', '.svn', 'node_modules',
        '__pycache__', '.vscode', '.idea', 'System Volume Information'
    }
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_video_file(self, file_path: str) -> bool:
        """
        Check if a file is a video file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if it's a video file, False otherwise
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.VIDEO_EXTENSIONS
    
    def should_ignore_folder(self, folder_name: str) -> bool:
        """
        Check if a folder should be ignored during scanning.
        
        Args:
            folder_name: Name of the folder
            
        Returns:
            True if folder should be ignored, False otherwise
        """
        return folder_name.lower() in {f.lower() for f in self.IGNORE_FOLDERS}
    
    def detect_media_folder_type(self, folder_path: str, max_depth: int = 3) -> MediaFolderInfo:
        """
        Analyze a folder to determine if it contains media and what type.
        
        Args:
            folder_path: Path to the folder to analyze
            max_depth: Maximum depth to scan for analysis
            
        Returns:
            MediaFolderInfo object with analysis results
        """
        folder_info = MediaFolderInfo(folder_path)
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return folder_info
        
        tv_indicators = 0
        movie_indicators = 0
        season_folders = 0
        
        try:
            # Quick scan to get basic stats
            for root, dirs, files in os.walk(folder_path):
                # Limit depth
                depth = root[len(folder_path):].count(os.sep)
                if depth >= max_depth:
                    dirs[:] = []  # Don't go deeper
                    continue
                
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore_folder(d)]
                
                folder_info.subdirectory_count += len(dirs)
                folder_info.total_file_count += len(files)
                
                # Check for season folders
                for dir_name in dirs:
                    if re.match(r'^[Ss]eason\s*\d+$', dir_name, re.IGNORECASE) or \
                       re.match(r'^[Ss]\d{1,2}$', dir_name):
                        season_folders += 1
                        tv_indicators += 2
                
                # Analyze files
                for file in files:
                    if self.is_video_file(file):
                        folder_info.media_file_count += 1
                        
                        # Store sample files for further analysis
                        if len(folder_info.sample_files) < 10:
                            file_path = os.path.join(root, file)
                            folder_info.sample_files.append(file_path)
                        
                        # Check for TV show patterns
                        season, episode, _ = self.extract_tv_info(file)
                        if season is not None or episode is not None:
                            tv_indicators += 1
                        else:
                            # Check for movie patterns (year in filename)
                            if self.extract_year(file):
                                movie_indicators += 1
            
            # Calculate confidence and determine type
            total_media = folder_info.media_file_count
            if total_media == 0:
                folder_info.detected_type = None
                folder_info.confidence_score = 0.0
            else:
                # TV show indicators
                tv_score = (tv_indicators + season_folders * 2) / max(total_media, 1)
                movie_score = movie_indicators / max(total_media, 1)
                
                # Adjust scores based on folder structure
                if season_folders > 0:
                    tv_score += 0.5
                
                # Determine type based on scores
                if tv_score > movie_score and tv_score > 0.3:
                    folder_info.detected_type = 'tv_shows'
                    folder_info.confidence_score = min(tv_score, 1.0)
                elif movie_score > tv_score and movie_score > 0.2:
                    folder_info.detected_type = 'movies'
                    folder_info.confidence_score = min(movie_score, 1.0)
                elif total_media > 0:
                    folder_info.detected_type = 'mixed'
                    folder_info.confidence_score = 0.5
                
                # Boost confidence for clear indicators
                if season_folders > 2:
                    folder_info.confidence_score = min(folder_info.confidence_score + 0.3, 1.0)
                
        except Exception as e:
            self.logger.error(f"Error analyzing folder {folder_path}: {e}")
        
        return folder_info
    
    def scan_plex_directory(self, base_path: str = "/media/plex") -> List[MediaFolderInfo]:
        """
        Scan the Plex base directory and identify media folders.
        
        Args:
            base_path: Base path to scan (default: /media/plex)
            
        Returns:
            List of MediaFolderInfo objects for detected media folders
        """
        media_folders = []
        
        if not os.path.exists(base_path):
            self.logger.warning(f"Plex directory not found: {base_path}")
            return media_folders
        
        self.logger.info(f"Scanning Plex directory: {base_path}")
        
        try:
            # Get all subdirectories
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                
                if not os.path.isdir(item_path) or self.should_ignore_folder(item):
                    continue
                
                # Analyze each subdirectory
                folder_info = self.detect_media_folder_type(item_path)
                
                # Only include folders with media content
                if folder_info.media_file_count > 0:
                    media_folders.append(folder_info)
                    self.logger.info(
                        f"Found media folder: {item} "
                        f"(Type: {folder_info.detected_type}, "
                        f"Files: {folder_info.media_file_count}, "
                        f"Confidence: {folder_info.confidence_score:.2f})"
                    )
        
        except Exception as e:
            self.logger.error(f"Error scanning Plex directory: {e}")
        
        # Sort by confidence score (highest first)
        media_folders.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return media_folders
    
    def extract_year(self, text: str) -> Optional[int]:
        """
        Extract year from text.
        
        Args:
            text: Text to search for year
            
        Returns:
            Year as integer or None if not found
        """
        match = re.search(self.YEAR_PATTERN, text)
        if match:
            return int(match.group(1))
        return None
    
    def extract_quality(self, text: str) -> Optional[str]:
        """
        Extract quality information from text.
        
        Args:
            text: Text to search for quality
            
        Returns:
            Quality string or None if not found
        """
        for pattern in self.QUALITY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_source(self, text: str) -> Optional[str]:
        """
        Extract source information from text.
        
        Args:
            text: Text to search for source
            
        Returns:
            Source string or None if not found
        """
        for pattern in self.SOURCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_tv_info(self, text: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Extract TV show season and episode information.
        
        Args:
            text: Text to search for TV info
            
        Returns:
            Tuple of (season, episode, episode_end) or (None, None, None)
        """
        for pattern in self.TV_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Handle different pattern types
                if 'Season' in pattern:  # Season X Episode Y
                    season = int(groups[0])
                    episode = int(groups[1])
                    episode_end = None
                elif pattern.startswith(r'^[Ee]') or pattern.startswith(r'^(\d'):  # Episode only
                    season = None  # Will be determined from folder structure
                    episode = int(groups[0])
                    episode_end = int(groups[1]) if groups[1] else None
                else:  # Standard SxE or SxxExx patterns
                    season = int(groups[0])
                    episode = int(groups[1])
                    episode_end = int(groups[2]) if len(groups) > 2 and groups[2] else None
                
                return season, episode, episode_end
        
        return None, None, None
    
    def clean_title(self, title: str) -> str:
        """
        Clean up title by removing quality, source, and other metadata.
        
        Args:
            title: Raw title to clean
            
        Returns:
            Cleaned title
        """
        # Remove quality indicators
        for pattern in self.QUALITY_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Remove source indicators
        for pattern in self.SOURCE_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Remove TV show patterns
        for pattern in self.TV_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Remove year (we'll extract it separately)
        title = re.sub(self.YEAR_PATTERN, '', title)
        
        # Remove common separators and clean up
        title = re.sub(r'[._\-\[\]()]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        title = title.strip()
        
        return title
    
    def parse_movie_file(self, file_path: str) -> MediaFileInfo:
        """
        Parse a movie file and extract metadata.
        
        Args:
            file_path: Path to the movie file
            
        Returns:
            MediaFileInfo object with parsed information
        """
        info = MediaFileInfo(file_path)
        info.media_type = 'movie'
        
        # Extract year first
        info.year = self.extract_year(info.name)
        
        # Clean title
        info.title = self.clean_title(info.name)
        
        # Extract quality and source
        info.quality = self.extract_quality(info.name)
        info.source = self.extract_source(info.name)
        
        self.logger.debug(f"Parsed movie: {info.title} ({info.year})")
        return info
    
    def parse_tv_file(self, file_path: str) -> MediaFileInfo:
        """
        Parse a TV show file and extract metadata.
        
        Args:
            file_path: Path to the TV show file
            
        Returns:
            MediaFileInfo object with parsed information
        """
        info = MediaFileInfo(file_path)
        info.media_type = 'tv'
        
        # Extract TV show information
        season, episode, episode_end = self.extract_tv_info(info.name)
        info.season = season
        info.episode = episode
        info.episode_end = episode_end
        
        # If season not found in filename, try to extract from directory structure
        if info.season is None:
            # Look for season information in parent directories
            path_parts = file_path.split(os.sep)
            for part in reversed(path_parts):
                season_match = re.search(r'[Ss]eason\s*(\d{1,2})', part, re.IGNORECASE)
                if season_match:
                    info.season = int(season_match.group(1))
                    break
                # Also check for S01, S1 patterns
                season_match = re.search(r'^[Ss](\d{1,2})$', part)
                if season_match:
                    info.season = int(season_match.group(1))
                    break
        
        # Extract year
        info.year = self.extract_year(info.name)
        
        # Clean title
        info.title = self.clean_title(info.name)
        
        # Extract quality and source
        info.quality = self.extract_quality(info.name)
        info.source = self.extract_source(info.name)
        
        self.logger.debug(f"Parsed TV: {info.title} S{info.season:02d}E{info.episode:02d}")
        return info
    
    def scan_directory(self, directory: str, media_type: str = 'auto') -> List[MediaFileInfo]:
        """
        Scan a directory for media files and parse them.
        
        Args:
            directory: Directory to scan
            media_type: Type of media ('movie', 'tv', or 'auto')
            
        Returns:
            List of MediaFileInfo objects
        """
        media_files = []
        
        if not os.path.exists(directory):
            self.logger.error(f"Directory not found: {directory}")
            return media_files
        
        self.logger.info(f"Scanning directory: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                if not self.is_video_file(file_path):
                    continue
                
                try:
                    if media_type == 'movie':
                        info = self.parse_movie_file(file_path)
                    elif media_type == 'tv':
                        info = self.parse_tv_file(file_path)
                    else:  # auto-detect
                        # Try to detect based on filename patterns
                        season, episode, _ = self.extract_tv_info(file)
                        if season is not None or episode is not None:
                            info = self.parse_tv_file(file_path)
                        else:
                            info = self.parse_movie_file(file_path)
                    
                    media_files.append(info)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing file {file_path}: {e}")
        
        self.logger.info(f"Found {len(media_files)} media files")
        return media_files 