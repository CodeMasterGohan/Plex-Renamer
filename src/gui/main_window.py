"""
Main GUI window for the Plex Media Renamer application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
from typing import List, Optional

from src.utils.config import Config
from src.utils.logger import get_logger
from src.core.file_parser import FileParser, MediaFileInfo
from src.core.renamer import MediaRenamer, RenameOperation
from src.gui.settings_dialog import SettingsDialog
from src.gui.preview_dialog import PreviewDialog

logger = get_logger(__name__)

class PlexRenamerApp:
    """Main application window."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main application window.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.config = Config()
        self.file_parser = FileParser()
        self.media_renamer = MediaRenamer(self.config)
        
        self.media_files: List[MediaFileInfo] = []
        self.rename_operations: List[RenameOperation] = []
        self.is_processing = False
        
        self.setup_ui()
        self.check_configuration()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.root.title("Plex Media Renamer")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main menu
        self.create_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Path selection frame
        path_frame = ttk.LabelFrame(main_frame, text="Media Paths", padding="10")
        path_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)
        
        # Media type selection
        ttk.Label(path_frame, text="Media Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.media_type_var = tk.StringVar(value="movies")
        media_type_frame = ttk.Frame(path_frame)
        media_type_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(media_type_frame, text="Movies", variable=self.media_type_var, 
                       value="movies").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(media_type_frame, text="TV Shows", variable=self.media_type_var, 
                       value="tv_shows").pack(side=tk.LEFT)
        
        # Path display
        ttk.Label(path_frame, text="Scan Path:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, state="readonly")
        path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(0, 10))
        
        ttk.Button(path_frame, text="Browse", command=self.browse_path).grid(row=1, column=2, pady=(10, 0))
        
        # Update path when media type changes
        self.media_type_var.trace('w', self.update_path_display)
        self.update_path_display()
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame, text="Scan Files", command=self.scan_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Preview Changes", command=self.preview_changes).pack(side=tk.LEFT, padx=(0, 10))
        
        self.dry_run_var = tk.BooleanVar(value=self.config.dry_run_mode)
        ttk.Checkbutton(control_frame, text="Dry Run Mode", variable=self.dry_run_var).pack(side=tk.LEFT, padx=(20, 10))
        
        ttk.Button(control_frame, text="Apply Changes", command=self.apply_changes).pack(side=tk.RIGHT)
        
        # File list frame
        list_frame = ttk.LabelFrame(main_frame, text="Scanned Files", padding="10")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for file list
        columns = ("Original", "New Name", "Status")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.file_tree.heading("#0", text="Type")
        self.file_tree.heading("Original", text="Original Path")
        self.file_tree.heading("New Name", text="Proposed Name")
        self.file_tree.heading("Status", text="Status")
        
        self.file_tree.column("#0", width=60, minwidth=60)
        self.file_tree.column("Original", width=300, minwidth=200)
        self.file_tree.column("New Name", width=300, minwidth=200)
        self.file_tree.column("Status", width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid treeview and scrollbars
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, padding="5")
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def update_path_display(self, *args):
        """Update the path display based on selected media type."""
        media_type = self.media_type_var.get()
        if media_type == "movies":
            path = self.config.movies_path
        else:
            path = self.config.tv_shows_path
        
        self.path_var.set(path or "Not configured")
    
    def browse_path(self):
        """Browse for a directory path."""
        current_path = self.path_var.get()
        if current_path == "Not configured":
            current_path = ""
        
        directory = filedialog.askdirectory(
            title="Select Media Directory",
            initialdir=current_path if current_path else None
        )
        
        if directory:
            media_type = self.media_type_var.get()
            if media_type == "movies":
                self.config.set('PATHS', 'movies_subfolder', os.path.relpath(directory, self.config.base_media_path) if self.config.base_media_path else directory)
            else:
                self.config.set('PATHS', 'tv_shows_subfolder', os.path.relpath(directory, self.config.base_media_path) if self.config.base_media_path else directory)
            
            self.config.save_config()
            self.update_path_display()
    
    def check_configuration(self):
        """Check if the application is properly configured."""
        if not self.config.tmdb_api_key and not self.config.tvdb_api_key:
            messagebox.showwarning(
                "Configuration Required",
                "Please configure your API keys in Settings before scanning files."
            )
        
        if not self.config.base_media_path:
            messagebox.showinfo(
                "Setup Required",
                "Please configure your media paths in Settings."
            )
    
    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.root, self.config)
        if dialog.result:
            # Refresh the media renamer with new config
            self.media_renamer = MediaRenamer(self.config)
            self.update_path_display()
            self.status_var.set("Configuration updated")
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Plex Media Renamer",
            "Plex Media Renamer v1.0\n\n"
            "A tool for renaming media files according to Plex naming conventions.\n\n"
            "Uses TMDB and TVDB APIs for metadata."
        )
    
    def scan_files(self):
        """Scan for media files in the selected directory."""
        if self.is_processing:
            return
        
        media_type = self.media_type_var.get()
        path = self.config.movies_path if media_type == "movies" else self.config.tv_shows_path
        
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", f"Path not found: {path}")
            return
        
        self.is_processing = True
        self.status_var.set("Scanning files...")
        self.clear_file_list()
        
        # Run scan in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._scan_files_thread, args=(path, media_type))
        thread.daemon = True
        thread.start()
    
    def _scan_files_thread(self, path: str, media_type: str):
        """Thread function for scanning files."""
        try:
            # Convert media type for parser
            parser_type = "movie" if media_type == "movies" else "tv"
            self.media_files = self.file_parser.scan_directory(path, parser_type)
            
            # Update UI in main thread
            self.root.after(0, self._update_file_list)
            
        except Exception as e:
            logger.error(f"Error scanning files: {e}")
            self.root.after(0, lambda: messagebox.showerror("Scan Error", f"Error scanning files: {e}"))
        
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.status_var.set(f"Found {len(self.media_files)} files"))
    
    def clear_file_list(self):
        """Clear the file list display."""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
    
    def _update_file_list(self):
        """Update the file list display with scanned files."""
        self.clear_file_list()
        
        for media_file in self.media_files:
            file_type = "📽️" if media_file.media_type == "movie" else "📺"
            relative_path = os.path.relpath(media_file.file_path)
            
            self.file_tree.insert("", tk.END, 
                                text=file_type,
                                values=(relative_path, "Pending analysis...", "Scanned"))
    
    def preview_changes(self):
        """Preview the planned rename operations."""
        if not self.media_files:
            messagebox.showwarning("No Files", "Please scan for files first.")
            return
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.status_var.set("Planning rename operations...")
        
        # Run planning in separate thread
        thread = threading.Thread(target=self._plan_operations_thread)
        thread.daemon = True
        thread.start()
    
    def _plan_operations_thread(self):
        """Thread function for planning rename operations."""
        try:
            self.rename_operations = self.media_renamer.plan_operations(self.media_files)
            
            # Update UI in main thread
            self.root.after(0, self._update_preview)
            
        except Exception as e:
            logger.error(f"Error planning operations: {e}")
            self.root.after(0, lambda: messagebox.showerror("Planning Error", f"Error planning operations: {e}"))
        
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.status_var.set(f"Planned {len(self.rename_operations)} operations"))
    
    def _update_preview(self):
        """Update the file list with planned operations."""
        # Clear current list
        self.clear_file_list()
        
        # Add operations to list
        for i, operation in enumerate(self.rename_operations):
            media_file = self.media_files[i]
            file_type = "📽️" if media_file.media_type == "movie" else "📺"
            
            relative_source = os.path.relpath(operation.source_path)
            relative_target = os.path.relpath(operation.target_path)
            
            self.file_tree.insert("", tk.END,
                                text=file_type,
                                values=(relative_source, relative_target, "Ready"))
        
        # Show preview dialog
        if self.rename_operations:
            dialog = PreviewDialog(self.root, self.rename_operations)
    
    def apply_changes(self):
        """Apply the planned rename operations."""
        if not self.rename_operations:
            messagebox.showwarning("No Operations", "Please preview changes first.")
            return
        
        dry_run = self.dry_run_var.get()
        action = "simulate" if dry_run else "execute"
        
        result = messagebox.askyesno(
            "Confirm Changes",
            f"Are you sure you want to {action} {len(self.rename_operations)} rename operations?"
        )
        
        if not result:
            return
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.status_var.set(f"{'Simulating' if dry_run else 'Executing'} operations...")
        
        # Run operations in separate thread
        thread = threading.Thread(target=self._execute_operations_thread, args=(dry_run,))
        thread.daemon = True
        thread.start()
    
    def _execute_operations_thread(self, dry_run: bool):
        """Thread function for executing rename operations."""
        try:
            results = self.media_renamer.execute_operations(self.rename_operations, dry_run)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._show_results(results, dry_run))
            
        except Exception as e:
            logger.error(f"Error executing operations: {e}")
            self.root.after(0, lambda: messagebox.showerror("Execution Error", f"Error executing operations: {e}"))
        
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def _show_results(self, results: dict, dry_run: bool):
        """Show the results of the operations."""
        action = "simulated" if dry_run else "executed"
        
        message = (f"Operations {action}:\n\n"
                  f"✅ Successful: {results['success']}\n"
                  f"❌ Failed: {results['failed']}\n"
                  f"⏭️ Skipped: {results['skipped']}")
        
        if results['failed'] > 0:
            messagebox.showwarning("Results", message)
        else:
            messagebox.showinfo("Results", message)
        
        # Update status display
        for i, operation in enumerate(self.rename_operations):
            item_id = self.file_tree.get_children()[i]
            status = "✅ Success" if operation.success else "❌ Failed"
            
            # Update the status column
            current_values = list(self.file_tree.item(item_id, "values"))
            current_values[2] = status
            self.file_tree.item(item_id, values=current_values) 