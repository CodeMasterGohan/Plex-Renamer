#!/usr/bin/env python3
"""
Test script for the Plex Media Renamer application.
This script can be used to test the application without actual media files or API keys.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.file_parser import FileParser, MediaFileInfo
from src.core.renamer import MediaRenamer
from src.utils.config import Config
from src.utils.logger import setup_logging

def create_test_media_structure():
    """Create a temporary directory structure with test media files."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="plex_test_")
    print(f"Created test directory: {temp_dir}")
    
    # Create directory structure
    movies_dir = os.path.join(temp_dir, "movies")
    tv_dir = os.path.join(temp_dir, "tv_shows")
    
    os.makedirs(movies_dir, exist_ok=True)
    os.makedirs(tv_dir, exist_ok=True)
    
    # Create test movie files
    movie_files = [
        "The.Avengers.2012.1080p.BluRay.x264.mkv",
        "Inception 2010 720p BDRip.mp4",
        "The Matrix (1999) [1080p].avi",
        "Pulp Fiction 1994.mkv"
    ]
    
    for movie_file in movie_files:
        file_path = os.path.join(movies_dir, movie_file)
        # Create empty files for testing
        Path(file_path).touch()
    
    # Create test TV show files
    tv_files = [
        "Breaking.Bad.S01E01.720p.HDTV.x264.mkv",
        "Game of Thrones - s02e05 - The Ghost of Harrenhal.mp4",
        "The Office US S03E12 Traveling Salesmen 1080p.avi",
        "Stranger Things 2016 1x08 Chapter Eight The Upside Down.mkv"
    ]
    
    for tv_file in tv_files:
        file_path = os.path.join(tv_dir, tv_file)
        Path(file_path).touch()
    
    return temp_dir

def test_file_parsing():
    """Test the file parsing functionality."""
    print("\n=== Testing File Parser ===")
    
    temp_dir = create_test_media_structure()
    parser = FileParser()
    
    try:
        # Test movie parsing
        print("\nTesting movie parsing:")
        movies_dir = os.path.join(temp_dir, "movies")
        movie_files = parser.scan_directory(movies_dir, "movie")
        
        for movie in movie_files:
            print(f"  {movie.filename} -> {movie.title} ({movie.year})")
        
        # Test TV show parsing
        print("\nTesting TV show parsing:")
        tv_dir = os.path.join(temp_dir, "tv_shows")
        tv_files = parser.scan_directory(tv_dir, "tv")
        
        for tv_show in tv_files:
            season = tv_show.season or "?"
            episode = tv_show.episode or "?"
            print(f"  {tv_show.filename} -> {tv_show.title} S{season:02d}E{episode:02d}")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up test directory: {temp_dir}")

def test_rename_planning():
    """Test the rename operation planning."""
    print("\n=== Testing Rename Planning ===")
    
    temp_dir = create_test_media_structure()
    
    try:
        # Create a test configuration
        config = Config()
        config.base_media_path = temp_dir
        config.set('PATHS', 'movies_subfolder', 'movies')
        config.set('PATHS', 'tv_shows_subfolder', 'tv_shows')
        
        # Initialize components (without API keys for testing)
        parser = FileParser()
        renamer = MediaRenamer(config)
        
        # Parse files
        movies_dir = os.path.join(temp_dir, "movies")
        tv_dir = os.path.join(temp_dir, "tv_shows")
        
        movie_files = parser.scan_directory(movies_dir, "movie")
        tv_files = parser.scan_directory(tv_dir, "tv")
        
        all_files = movie_files + tv_files
        
        # Plan operations
        print("\nPlanning rename operations:")
        operations = renamer.plan_operations(all_files)
        
        for operation in operations:
            source_rel = os.path.relpath(operation.source_path, temp_dir)
            target_rel = os.path.relpath(operation.target_path, temp_dir)
            print(f"  {source_rel} -> {target_rel}")
        
        # Test dry run execution
        print("\nTesting dry run execution:")
        results = renamer.execute_operations(operations, dry_run=True)
        print(f"Results: {results}")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up test directory: {temp_dir}")

def main():
    """Main test function."""
    print("Plex Media Renamer - Test Suite")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    
    try:
        test_file_parsing()
        test_rename_planning()
        print("\n✅ All tests completed successfully!")
        print("\nTo run the full GUI application, use: python main.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 