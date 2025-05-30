#!/usr/bin/env python3
"""
Plex Media Renamer Web Application
Flask backend API server
"""

import os
import sys
import json
import traceback
from datetime import datetime
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.utils.logger import setup_logging, get_logger
from src.core.file_parser import FileParser, MediaFileInfo
from src.core.renamer import MediaRenamer, RenameOperation
from src.api.tmdb import TMDBClient
from src.api.tvdb import TVDBClient

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
CORS(app)

# Global variables
config = Config()
file_parser = FileParser()
media_renamer = MediaRenamer(config)
current_scan_results = []
current_rename_operations = []
scan_status = {'is_scanning': False, 'progress': 0, 'message': 'Ready'}

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Routes

@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    try:
        config_data = {
            'tmdb_api_key': bool(config.tmdb_api_key),  # Don't expose actual key
            'tvdb_api_key': bool(config.tvdb_api_key),  # Don't expose actual key
            'base_media_path': config.base_media_path,
            'movies_path': config.movies_path,
            'tv_shows_path': config.tv_shows_path,
            'dry_run_mode': config.dry_run_mode,
            'create_movie_folders': config.get_boolean('MOVIES', 'create_movie_folders', True),
            'include_episode_title': config.get_boolean('TV_SHOWS', 'include_episode_title', True),
            'include_series_id': config.get_boolean('TV_SHOWS', 'include_series_id', False),
            'preferred_id_source': config.get('TV_SHOWS', 'preferred_id_source', 'tvdb'),
            'preferred_language': config.get('API', 'preferred_language', 'en-US')
        }
        return jsonify({'success': True, 'config': config_data})
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    try:
        data = request.get_json()
        
        # Update API keys
        if 'tmdb_api_key' in data:
            config.set('API', 'tmdb_api_key', data['tmdb_api_key'])
        if 'tvdb_api_key' in data:
            config.set('API', 'tvdb_api_key', data['tvdb_api_key'])
        
        # Update paths
        if 'base_media_path' in data:
            config.set('PATHS', 'base_media_path', data['base_media_path'])
        if 'movies_subfolder' in data:
            config.set('PATHS', 'movies_subfolder', data['movies_subfolder'])
        if 'tv_shows_subfolder' in data:
            config.set('PATHS', 'tv_shows_subfolder', data['tv_shows_subfolder'])
        
        # Update other settings
        if 'dry_run_mode' in data:
            config.set('GENERAL', 'dry_run_mode', str(data['dry_run_mode']).lower())
        if 'create_movie_folders' in data:
            config.set('MOVIES', 'create_movie_folders', str(data['create_movie_folders']).lower())
        if 'include_episode_title' in data:
            config.set('TV_SHOWS', 'include_episode_title', str(data['include_episode_title']).lower())
        if 'include_series_id' in data:
            config.set('TV_SHOWS', 'include_series_id', str(data['include_series_id']).lower())
        if 'preferred_id_source' in data:
            config.set('TV_SHOWS', 'preferred_id_source', data['preferred_id_source'])
        if 'preferred_language' in data:
            config.set('API', 'preferred_language', data['preferred_language'])
        
        # Save configuration
        config.save_config()
        
        # Reinitialize media renamer with new config
        global media_renamer
        media_renamer = MediaRenamer(config)
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def scan_files():
    """Scan media files."""
    try:
        data = request.get_json()
        media_type = data.get('media_type', 'movies')
        scan_path = data.get('scan_path', '')
        
        if not scan_path:
            if media_type == 'movies':
                scan_path = config.movies_path
            else:
                scan_path = config.tv_shows_path
        
        if not scan_path or not os.path.exists(scan_path):
            return jsonify({'success': False, 'error': 'Invalid scan path'}), 400
        
        # Start scanning in a separate thread
        def scan_thread():
            global current_scan_results, scan_status, current_rename_operations
            try:
                scan_status['is_scanning'] = True
                scan_status['message'] = 'Scanning files...'
                scan_status['progress'] = 0
                
                # Scan for media files
                media_files = file_parser.scan_directory(scan_path, media_type)
                current_scan_results = media_files
                
                scan_status['progress'] = 50
                scan_status['message'] = 'Generating rename operations...'
                
                # Generate rename operations
                operations = []
                for i, media_file in enumerate(media_files):
                    try:
                        if media_type == 'movies':
                            metadata = media_renamer.get_movie_metadata(media_file)
                            new_name = media_renamer.generate_movie_name(media_file, metadata)
                            target_dir = os.path.dirname(media_file.file_path)
                            if config.get_boolean('MOVIES', 'create_movie_folders', True):
                                movie_folder = os.path.join(os.path.dirname(target_dir), new_name)
                                target_path = os.path.join(movie_folder, f"{new_name}{media_file.extension}")
                            else:
                                target_path = os.path.join(target_dir, f"{new_name}{media_file.extension}")
                        else:
                            show_metadata, episode_metadata = media_renamer.get_tv_show_metadata(media_file)
                            
                            new_name = media_renamer.generate_tv_episode_name(
                                media_file, show_metadata, episode_metadata
                            )
                            
                            # Generate folder structure
                            if show_metadata:
                                show_folder = media_renamer.generate_tv_show_folder_name(show_metadata, media_file)
                            else:
                                show_folder = media_file.title
                            
                            season_folder = f"Season {media_file.season:02d}" if media_file.season else "Season 01"
                            target_dir = os.path.join(config.tv_shows_path, show_folder, season_folder)
                            target_path = os.path.join(target_dir, f"{new_name}{media_file.extension}")
                        
                        operation = RenameOperation(media_file.file_path, target_path)
                        operation.metadata = {
                            'movie_metadata': metadata if media_type == 'movies' else None,
                            'show_metadata': show_metadata if media_type == 'tv_shows' else None,
                            'episode_metadata': episode_metadata if media_type == 'tv_shows' else None,
                            'media_info': {
                                'title': media_file.title,
                                'year': media_file.year,
                                'season': media_file.season,
                                'episode': media_file.episode,
                                'extension': media_file.extension
                            }
                        }
                        operations.append(operation)
                        
                        # Update progress
                        progress = 50 + (i + 1) / len(media_files) * 50
                        scan_status['progress'] = int(progress)
                        
                    except Exception as e:
                        logger.error(f"Error processing {media_file.file_path}: {e}")
                
                current_rename_operations = operations
                scan_status['is_scanning'] = False
                scan_status['progress'] = 100
                scan_status['message'] = f'Scan complete. Found {len(media_files)} files, {len(operations)} operations ready.'
                
            except Exception as e:
                logger.error(f"Error during scan: {e}")
                scan_status['is_scanning'] = False
                scan_status['message'] = f'Scan error: {str(e)}'
        
        Thread(target=scan_thread, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Scan started'})
    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan/status', methods=['GET'])
def get_scan_status():
    """Get current scan status."""
    return jsonify({
        'success': True,
        'status': scan_status,
        'files_count': len(current_scan_results),
        'operations_count': len(current_rename_operations)
    })

@app.route('/api/scan/results', methods=['GET'])
def get_scan_results():
    """Get scan results."""
    try:
        results = []
        for i, operation in enumerate(current_rename_operations):
            media_info = operation.metadata.get('media_info', {})
            result = {
                'id': i,
                'source_path': operation.source_path,
                'target_path': operation.target_path,
                'filename': os.path.basename(operation.source_path),
                'new_filename': os.path.basename(operation.target_path),
                'title': media_info.get('title', ''),
                'year': media_info.get('year', ''),
                'season': media_info.get('season', ''),
                'episode': media_info.get('episode', ''),
                'status': 'Ready',
                'metadata': operation.metadata
            }
            results.append(result)
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error getting scan results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rename', methods=['POST'])
def apply_rename():
    """Apply rename operations."""
    try:
        data = request.get_json()
        dry_run = data.get('dry_run', config.dry_run_mode)
        selected_operations = data.get('operations', [])
        
        if not selected_operations:
            # Apply all operations if none specified
            operations_to_apply = current_rename_operations
        else:
            # Apply only selected operations
            operations_to_apply = [current_rename_operations[i] for i in selected_operations 
                                 if i < len(current_rename_operations)]
        
        results = []
        
        for operation in operations_to_apply:
            try:
                if dry_run:
                    # Simulate the operation
                    operation.success = True
                    operation.error_message = None
                    result = {
                        'source_path': operation.source_path,
                        'target_path': operation.target_path,
                        'success': True,
                        'message': 'Dry run - would rename file'
                    }
                else:
                    # Actually perform the operation
                    success, error = media_renamer.apply_rename_operation(operation)
                    operation.success = success
                    operation.error_message = error
                    
                    result = {
                        'source_path': operation.source_path,
                        'target_path': operation.target_path,
                        'success': success,
                        'message': 'Renamed successfully' if success else f'Error: {error}'
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error applying operation {operation.source_path}: {e}")
                result = {
                    'source_path': operation.source_path,
                    'target_path': operation.target_path,
                    'success': False,
                    'message': f'Error: {str(e)}'
                }
                results.append(result)
        
        successful_operations = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful_operations,
                'failed': len(results) - successful_operations,
                'dry_run': dry_run
            }
        })
        
    except Exception as e:
        logger.error(f"Error applying rename operations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse', methods=['POST'])
def browse_directory():
    """Browse directory contents."""
    try:
        data = request.get_json()
        path = data.get('path', '/media/plex')
        
        if not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Directory does not exist'}), 400
        
        if not os.path.isdir(path):
            return jsonify({'success': False, 'error': 'Path is not a directory'}), 400
        
        directories = []
        files = []
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    directories.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory'
                    })
                elif os.path.isfile(item_path):
                    files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'file',
                        'size': os.path.getsize(item_path)
                    })
        except PermissionError:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        directories.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            'success': True,
            'path': path,
            'parent': os.path.dirname(path) if path != '/' else None,
            'directories': directories,
            'files': files
        })
        
    except Exception as e:
        logger.error(f"Error browsing directory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Plex Media Renamer Web Application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 