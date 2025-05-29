"""
Settings dialog for the Plex Media Renamer application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SettingsDialog:
    """Settings configuration dialog."""
    
    def __init__(self, parent: tk.Tk, config: Config):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent window
            config: Configuration object
        """
        self.parent = parent
        self.config = config
        self.result = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
        self.load_settings()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # API Settings tab
        api_frame = ttk.Frame(notebook, padding="20")
        notebook.add(api_frame, text="API Settings")
        self.setup_api_tab(api_frame)
        
        # Paths tab
        paths_frame = ttk.Frame(notebook, padding="20")
        notebook.add(paths_frame, text="Paths")
        self.setup_paths_tab(paths_frame)
        
        # Movies tab
        movies_frame = ttk.Frame(notebook, padding="20")
        notebook.add(movies_frame, text="Movies")
        self.setup_movies_tab(movies_frame)
        
        # TV Shows tab
        tv_frame = ttk.Frame(notebook, padding="20")
        notebook.add(tv_frame, text="TV Shows")
        self.setup_tv_tab(tv_frame)
        
        # General tab
        general_frame = ttk.Frame(notebook, padding="20")
        notebook.add(general_frame, text="General")
        self.setup_general_tab(general_frame)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.save_and_close).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Test APIs", command=self.test_apis).pack(side=tk.LEFT)
    
    def setup_api_tab(self, parent):
        """Set up the API settings tab."""
        # TMDB API
        ttk.Label(parent, text="TMDB API Key:", font=("", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.tmdb_key_var = tk.StringVar()
        tmdb_entry = ttk.Entry(parent, textvariable=self.tmdb_key_var, width=50, show="*")
        tmdb_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(parent, text="Get your TMDB API key from: https://www.themoviedb.org/settings/api", 
                 foreground="blue").grid(row=2, column=0, sticky=tk.W, pady=(0, 20))
        
        # TVDB API
        ttk.Label(parent, text="TVDB API Key:", font=("", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.tvdb_key_var = tk.StringVar()
        tvdb_entry = ttk.Entry(parent, textvariable=self.tvdb_key_var, width=50, show="*")
        tvdb_entry.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(parent, text="Get your TVDB API key from: https://thetvdb.com/dashboard/account/apikey", 
                 foreground="blue").grid(row=5, column=0, sticky=tk.W, pady=(0, 20))
        
        # Language
        ttk.Label(parent, text="Preferred Language:", font=("", 10, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        self.language_var = tk.StringVar()
        language_combo = ttk.Combobox(parent, textvariable=self.language_var, width=20, state="readonly")
        language_combo['values'] = ('en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'ja-JP', 'ko-KR', 'pt-BR', 'ru-RU', 'zh-CN')
        language_combo.grid(row=7, column=0, sticky=tk.W, pady=(0, 10))
        
        # Configure column weight
        parent.columnconfigure(0, weight=1)
    
    def setup_paths_tab(self, parent):
        """Set up the paths settings tab."""
        # Base media path
        ttk.Label(parent, text="Base Media Path:", font=("", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(parent)
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        path_frame.columnconfigure(0, weight=1)
        
        self.base_path_var = tk.StringVar()
        base_path_entry = ttk.Entry(path_frame, textvariable=self.base_path_var)
        base_path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(path_frame, text="Browse", command=self.browse_base_path).grid(row=0, column=1)
        
        ttk.Label(parent, text="Example: Z:\\Plex or /mnt/media", foreground="gray").grid(row=2, column=0, sticky=tk.W, pady=(0, 20))
        
        # Movies subfolder
        ttk.Label(parent, text="Movies Subfolder:", font=("", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.movies_subfolder_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.movies_subfolder_var, width=30).grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        
        # TV Shows subfolder
        ttk.Label(parent, text="TV Shows Subfolder:", font=("", 10, "bold")).grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.tv_subfolder_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.tv_subfolder_var, width=30).grid(row=6, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(parent, text="Note: Subfolders are relative to the base media path", 
                 foreground="gray").grid(row=7, column=0, sticky=tk.W, pady=(10, 0))
        
        # Configure column weight
        parent.columnconfigure(0, weight=1)
    
    def setup_movies_tab(self, parent):
        """Set up the movies settings tab."""
        # Create movie folders
        self.create_movie_folders_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Create individual folders for each movie", 
                       variable=self.create_movie_folders_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(parent, text="When enabled: Movie Title (Year)/Movie Title (Year).ext\n"
                              "When disabled: Movie Title (Year).ext", 
                 foreground="gray").grid(row=1, column=0, sticky=tk.W, pady=(0, 20))
        
        # Include year in folder name
        self.include_year_in_folder_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Include year in movie folder names", 
                       variable=self.include_year_in_folder_var).grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Preview
        preview_frame = ttk.LabelFrame(parent, text="Naming Preview", padding="10")
        preview_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.movie_preview_var = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.movie_preview_var, foreground="blue").pack()
        
        # Update preview when settings change
        self.create_movie_folders_var.trace('w', self.update_movie_preview)
        self.include_year_in_folder_var.trace('w', self.update_movie_preview)
        
        # Configure column weight
        parent.columnconfigure(0, weight=1)
    
    def setup_tv_tab(self, parent):
        """Set up the TV shows settings tab."""
        # Include episode title
        self.include_episode_title_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Include episode titles in filenames", 
                       variable=self.include_episode_title_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Include series ID
        self.include_series_id_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Include series ID in folder names", 
                       variable=self.include_series_id_var).grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Preferred ID source
        ttk.Label(parent, text="Preferred ID Source:", font=("", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self.preferred_id_source_var = tk.StringVar()
        id_frame = ttk.Frame(parent)
        id_frame.grid(row=3, column=0, sticky=tk.W, pady=(0, 20))
        
        ttk.Radiobutton(id_frame, text="TVDB", variable=self.preferred_id_source_var, 
                       value="tvdb").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(id_frame, text="TMDB", variable=self.preferred_id_source_var, 
                       value="tmdb").pack(side=tk.LEFT)
        
        # Preview
        preview_frame = ttk.LabelFrame(parent, text="Naming Preview", padding="10")
        preview_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.tv_preview_var = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.tv_preview_var, foreground="blue").pack()
        
        # Update preview when settings change
        self.include_episode_title_var.trace('w', self.update_tv_preview)
        self.include_series_id_var.trace('w', self.update_tv_preview)
        self.preferred_id_source_var.trace('w', self.update_tv_preview)
        
        # Configure column weight
        parent.columnconfigure(0, weight=1)
    
    def setup_general_tab(self, parent):
        """Set up the general settings tab."""
        # Dry run mode
        self.dry_run_mode_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable dry run mode by default", 
                       variable=self.dry_run_mode_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(parent, text="Dry run mode previews changes without actually renaming files", 
                 foreground="gray").grid(row=1, column=0, sticky=tk.W, pady=(0, 20))
        
        # Backup original names
        self.backup_original_names_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Backup original filenames", 
                       variable=self.backup_original_names_var).grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(parent, text="Creates a text file with original filenames for reference", 
                 foreground="gray").grid(row=3, column=0, sticky=tk.W, pady=(0, 20))
        
        # Log level
        ttk.Label(parent, text="Log Level:", font=("", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.log_level_var = tk.StringVar()
        log_combo = ttk.Combobox(parent, textvariable=self.log_level_var, width=15, state="readonly")
        log_combo['values'] = ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_combo.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        
        # Configure column weight
        parent.columnconfigure(0, weight=1)
    
    def browse_base_path(self):
        """Browse for base media path."""
        directory = filedialog.askdirectory(
            title="Select Base Media Directory",
            initialdir=self.base_path_var.get() if self.base_path_var.get() else None
        )
        
        if directory:
            self.base_path_var.set(directory)
    
    def update_movie_preview(self, *args):
        """Update the movie naming preview."""
        if self.create_movie_folders_var.get():
            if self.include_year_in_folder_var.get():
                preview = "movies/Avengers Endgame (2019)/Avengers Endgame (2019).mkv"
            else:
                preview = "movies/Avengers Endgame/Avengers Endgame (2019).mkv"
        else:
            preview = "movies/Avengers Endgame (2019).mkv"
        
        self.movie_preview_var.set(preview)
    
    def update_tv_preview(self, *args):
        """Update the TV show naming preview."""
        show_name = "Breaking Bad (2008)"
        if self.include_series_id_var.get():
            id_source = self.preferred_id_source_var.get() or "tvdb"
            show_name += f" {{{id_source}-12345}}"
        
        episode_name = "Breaking Bad - s01e01"
        if self.include_episode_title_var.get():
            episode_name += " - Pilot"
        
        preview = f"tv_shows/{show_name}/Season 01/{episode_name}.mkv"
        self.tv_preview_var.set(preview)
    
    def load_settings(self):
        """Load current settings into the dialog."""
        # API settings
        self.tmdb_key_var.set(self.config.tmdb_api_key)
        self.tvdb_key_var.set(self.config.tvdb_api_key)
        self.language_var.set(self.config.get('API', 'preferred_language', 'en-US'))
        
        # Paths
        self.base_path_var.set(self.config.base_media_path)
        self.movies_subfolder_var.set(self.config.get('PATHS', 'movies_subfolder', 'movies'))
        self.tv_subfolder_var.set(self.config.get('PATHS', 'tv_shows_subfolder', 'tv_shows'))
        
        # Movies
        self.create_movie_folders_var.set(self.config.get_boolean('MOVIES', 'create_movie_folders', True))
        self.include_year_in_folder_var.set(self.config.get_boolean('MOVIES', 'include_year_in_folder', True))
        
        # TV Shows
        self.include_episode_title_var.set(self.config.get_boolean('TV_SHOWS', 'include_episode_title', True))
        self.include_series_id_var.set(self.config.get_boolean('TV_SHOWS', 'include_series_id', False))
        self.preferred_id_source_var.set(self.config.get('TV_SHOWS', 'preferred_id_source', 'tvdb'))
        
        # General
        self.dry_run_mode_var.set(self.config.get_boolean('GENERAL', 'dry_run_mode', True))
        self.backup_original_names_var.set(self.config.get_boolean('GENERAL', 'backup_original_names', True))
        self.log_level_var.set(self.config.get('GENERAL', 'log_level', 'INFO'))
        
        # Update previews
        self.update_movie_preview()
        self.update_tv_preview()
    
    def save_settings(self):
        """Save settings to configuration."""
        # API settings
        self.config.tmdb_api_key = self.tmdb_key_var.get().strip()
        self.config.tvdb_api_key = self.tvdb_key_var.get().strip()
        self.config.set('API', 'preferred_language', self.language_var.get())
        
        # Paths
        self.config.base_media_path = self.base_path_var.get().strip()
        self.config.set('PATHS', 'movies_subfolder', self.movies_subfolder_var.get().strip())
        self.config.set('PATHS', 'tv_shows_subfolder', self.tv_subfolder_var.get().strip())
        
        # Movies
        self.config.set_boolean('MOVIES', 'create_movie_folders', self.create_movie_folders_var.get())
        self.config.set_boolean('MOVIES', 'include_year_in_folder', self.include_year_in_folder_var.get())
        
        # TV Shows
        self.config.set_boolean('TV_SHOWS', 'include_episode_title', self.include_episode_title_var.get())
        self.config.set_boolean('TV_SHOWS', 'include_series_id', self.include_series_id_var.get())
        self.config.set('TV_SHOWS', 'preferred_id_source', self.preferred_id_source_var.get())
        
        # General
        self.config.set_boolean('GENERAL', 'dry_run_mode', self.dry_run_mode_var.get())
        self.config.set_boolean('GENERAL', 'backup_original_names', self.backup_original_names_var.get())
        self.config.set('GENERAL', 'log_level', self.log_level_var.get())
        
        # Save to file
        self.config.save_config()
    
    def test_apis(self):
        """Test API connectivity."""
        # This is a placeholder for API testing
        # In a real implementation, you would test the APIs here
        messagebox.showinfo("API Test", "API testing functionality would be implemented here.\n\n"
                                       "This would verify that the provided API keys are valid.")
    
    def save_and_close(self):
        """Save settings and close dialog."""
        try:
            self.save_settings()
            self.result = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = False
        self.dialog.destroy() 