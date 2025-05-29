"""
Preview dialog for showing planned rename operations.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import List
from src.core.renamer import RenameOperation
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PreviewDialog:
    """Preview dialog for rename operations."""
    
    def __init__(self, parent: tk.Tk, operations: List[RenameOperation]):
        """
        Initialize the preview dialog.
        
        Args:
            parent: Parent window
            operations: List of RenameOperation objects to preview
        """
        self.parent = parent
        self.operations = operations
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preview Rename Operations")
        self.dialog.geometry("1000x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 25,
            parent.winfo_rooty() + 25
        ))
        
        self.setup_ui()
        self.populate_data()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and summary
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Rename Operations Preview", 
                 font=("", 12, "bold")).pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text=f"Total operations: {len(self.operations)}", 
                 font=("", 10)).pack(side=tk.RIGHT)
        
        # Operations list frame
        list_frame = ttk.LabelFrame(main_frame, text="Planned Operations", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure grid
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for operations
        columns = ("Source", "Target", "Type", "Status")
        self.operations_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Configure columns
        self.operations_tree.heading("Source", text="Current Location")
        self.operations_tree.heading("Target", text="New Location")
        self.operations_tree.heading("Type", text="Type")
        self.operations_tree.heading("Status", text="Status")
        
        self.operations_tree.column("Source", width=350, minwidth=200)
        self.operations_tree.column("Target", width=350, minwidth=200)
        self.operations_tree.column("Type", width=80, minwidth=60)
        self.operations_tree.column("Status", width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.operations_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.operations_tree.xview)
        self.operations_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid treeview and scrollbars
        self.operations_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Details frame
        details_frame = ttk.LabelFrame(main_frame, text="Operation Details", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text widget for details
        self.details_text = tk.Text(details_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.operations_tree.bind('<<TreeviewSelect>>', self.on_selection_change)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Close", command=self.close_dialog).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Export List", command=self.export_list).pack(side=tk.LEFT)
    
    def populate_data(self):
        """Populate the treeview with operation data."""
        for i, operation in enumerate(self.operations):
            # Determine operation type and status
            op_type = "Movie" if "movies" in operation.target_path.lower() else "TV Show"
            status = "Ready"
            
            # Get relative paths for display
            source_rel = os.path.relpath(operation.source_path)
            target_rel = os.path.relpath(operation.target_path)
            
            # Insert item
            item_id = self.operations_tree.insert("", tk.END, 
                                                 values=(source_rel, target_rel, op_type, status))
            
            # Color-code based on operation type
            if op_type == "Movie":
                self.operations_tree.set(item_id, "Type", "🎬 Movie")
            else:
                self.operations_tree.set(item_id, "Type", "📺 TV Show")
    
    def on_selection_change(self, event):
        """Handle selection change in the treeview."""
        selection = self.operations_tree.selection()
        if not selection:
            return
        
        # Get selected item index
        item = selection[0]
        item_index = self.operations_tree.index(item)
        
        if 0 <= item_index < len(self.operations):
            operation = self.operations[item_index]
            self.show_operation_details(operation)
    
    def show_operation_details(self, operation: RenameOperation):
        """Show detailed information about an operation."""
        # Enable text widget for editing
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        # Format details
        details = []
        details.append(f"Source Path: {operation.source_path}")
        details.append(f"Target Path: {operation.target_path}")
        details.append(f"Operation Type: {operation.operation_type.title()}")
        
        # Show metadata if available
        if hasattr(operation, 'metadata') and operation.metadata:
            details.append("\nMetadata:")
            
            # Movie metadata
            if isinstance(operation.metadata, dict) and 'title' in operation.metadata:
                metadata = operation.metadata
                details.append(f"  Title: {metadata.get('title', 'N/A')}")
                details.append(f"  Release Date: {metadata.get('release_date', 'N/A')}")
                details.append(f"  Overview: {metadata.get('overview', 'N/A')[:100]}...")
            
            # TV show metadata
            elif isinstance(operation.metadata, dict) and 'show' in operation.metadata:
                show_meta = operation.metadata.get('show', {})
                episode_meta = operation.metadata.get('episode', {})
                
                if show_meta:
                    details.append(f"  Show: {show_meta.get('name', show_meta.get('title', 'N/A'))}")
                    details.append(f"  First Air Date: {show_meta.get('first_air_date', show_meta.get('first_air_time', 'N/A'))}")
                    details.append(f"  Overview: {show_meta.get('overview', 'N/A')[:100]}...")
                
                if episode_meta:
                    details.append(f"  Episode: {episode_meta.get('name', episode_meta.get('title', 'N/A'))}")
                    details.append(f"  Episode Overview: {episode_meta.get('overview', 'N/A')[:100]}...")
        
        # Directory creation info
        target_dir = os.path.dirname(operation.target_path)
        if not os.path.exists(target_dir):
            details.append(f"\nNew directory will be created: {target_dir}")
        
        # File size info (if source exists)
        if os.path.exists(operation.source_path):
            try:
                size_bytes = os.path.getsize(operation.source_path)
                size_mb = size_bytes / (1024 * 1024)
                details.append(f"\nFile size: {size_mb:.2f} MB")
            except:
                pass
        
        # Insert details into text widget
        self.details_text.insert(tk.END, "\n".join(details))
        
        # Disable text widget
        self.details_text.config(state=tk.DISABLED)
    
    def export_list(self):
        """Export the operations list to a text file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Export Operations List",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Plex Media Renamer - Planned Operations\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, operation in enumerate(self.operations, 1):
                        f.write(f"Operation {i}:\n")
                        f.write(f"  Source: {operation.source_path}\n")
                        f.write(f"  Target: {operation.target_path}\n")
                        f.write(f"  Type: {operation.operation_type}\n")
                        
                        if hasattr(operation, 'metadata') and operation.metadata:
                            f.write("  Metadata: Available\n")
                        
                        f.write("\n")
                
                logger.info(f"Operations list exported to {filename}")
                
                from tkinter import messagebox
                messagebox.showinfo("Export Complete", f"Operations list exported to:\n{filename}")
                
            except Exception as e:
                logger.error(f"Error exporting operations list: {e}")
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export operations list:\n{e}")
    
    def close_dialog(self):
        """Close the preview dialog."""
        self.dialog.destroy() 