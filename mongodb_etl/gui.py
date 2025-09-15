"""
MongoDB ETL GUI Application

A graphical interface for the MongoDB ETL tool that allows users to:
1. Connect to a MongoDB database
2. Select collections to extract
3. Choose output formats (JSON, CSV, Parquet)
4. Run the ETL process with visual feedback
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add package to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import ETL components
try:
    # When installed as a package
    from mongodb_etl import MongoDBETL
    from mongodb_etl.transformers.data_transformer import DataTransformer
    from mongodb_etl.loaders.data_loader import DataLoader
    from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
    from mongodb_etl.validators.data_validator import DataValidator
except ImportError:
    # When running from source
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from mongodb_etl.mongodb_etl import MongoDBETL
    from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
    from mongodb_etl.transformers.data_transformer import DataTransformer
    from mongodb_etl.loaders.data_loader import DataLoader
    from mongodb_etl.validators.data_validator import DataValidator

class MongoDBETLApp(tk.Tk):
    """
    GUI application for MongoDB ETL operations.
    """
    
    def __init__(self):
        """Initialize the application window and components."""
        super().__init__()
        
        # Configure the main window
        self.title("MongoDB ETL Tool")
        self.geometry("800x600")
        self.minsize(600, 500)
        
        # Add icon if available
        try:
            self.iconbitmap("mongodb_etl/resources/icon.ico")
        except:
            pass
        
        # Status variables - initialize these first
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        
        # Keep track of last output file
        self.last_output_file = None
        self.last_output_format = None
        
        # MongoDB connection variables
        self.uri_var = tk.StringVar(value="mongodb://localhost:27017/")
        self.db_var = tk.StringVar()
        self.collections = []
        self.selected_collection = tk.StringVar()
        
        # Output settings variables
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "output_data"))
        self.output_format_var = tk.StringVar(value="json")
        self.split_data_var = tk.BooleanVar(value=False)
        
        # Query variables
        self.query_filter_var = tk.StringVar(value="{}")
        self.limit_var = tk.StringVar(value="0")
        self.geo_field_var = tk.StringVar()
        self.use_geo_var = tk.BooleanVar(value=False)
        
        # Create the notebook
        self.notebook = ttk.Notebook(self)
        self.connection_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)
        self.execution_tab = ttk.Frame(self.notebook)
        self.output_viewer_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.connection_tab, text="Connection")
        self.notebook.add(self.data_tab, text="Data Selection")
        self.notebook.add(self.output_tab, text="Output Settings")
        self.notebook.add(self.execution_tab, text="Run ETL")
        self.notebook.add(self.output_viewer_tab, text="Output Viewer")
        # Alias for viewer content container used elsewhere in the code
        self.output_viewer_frame = self.output_viewer_tab
        
        # Create the main interface
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create all the widgets for the application."""
        # Main notebook and tabs were created in __init__
        
        # ------ Connection Tab ------
        # MongoDB URI input
        ttk.Label(self.connection_tab, text="MongoDB URI:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Entry(self.connection_tab, textvariable=self.uri_var, width=50).grid(row=0, column=1, padx=10, pady=5)
        
        # Database selection
        ttk.Label(self.connection_tab, text="Database:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.db_combo = ttk.Combobox(self.connection_tab, textvariable=self.db_var, width=30)
        self.db_combo.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Connect button
        self.connect_btn = ttk.Button(self.connection_tab, text="Connect", command=self.connect_to_mongodb)
        self.connect_btn.grid(row=1, column=2, padx=10, pady=5)
        
        # ------ Data Selection Tab ------
        # Collection selection
        ttk.Label(self.data_tab, text="Collection:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.collection_combo = ttk.Combobox(self.data_tab, textvariable=self.selected_collection, width=30, state="disabled")
        self.collection_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Query filter
        ttk.Label(self.data_tab, text="Query Filter (JSON):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Entry(self.data_tab, textvariable=self.query_filter_var, width=50).grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="we")
        
        # Document limit
        ttk.Label(self.data_tab, text="Limit (0 for all):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ttk.Entry(self.data_tab, textvariable=self.limit_var, width=10).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Geospatial options
        ttk.Checkbutton(self.data_tab, text="Use Geospatial Queries", variable=self.use_geo_var, 
                         command=self._toggle_geo_options).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.geo_frame = ttk.LabelFrame(self.data_tab, text="Geospatial Settings")
        self.geo_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="we")
        self.geo_frame.grid_remove()  # Hide initially
        
        ttk.Label(self.geo_frame, text="Coordinates Field:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Entry(self.geo_frame, textvariable=self.geo_field_var, width=30).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Preview button
        self.preview_btn = ttk.Button(self.data_tab, text="Preview Data", command=self.preview_data, state="disabled")
        self.preview_btn.grid(row=5, column=0, padx=10, pady=10)
        
        # ------ Output Settings Tab ------
        # Output directory
        ttk.Label(self.output_tab, text="Output Directory:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Entry(self.output_tab, textvariable=self.output_dir_var, width=50).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(self.output_tab, text="Browse...", command=self.browse_output_dir).grid(row=0, column=2, padx=10, pady=5)
        
        # Output format
        ttk.Label(self.output_tab, text="Output Format:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        format_frame = ttk.Frame(self.output_tab)
        format_frame.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Radiobutton(format_frame, text="JSON", variable=self.output_format_var, value="json").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format_var, value="csv").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="Parquet", variable=self.output_format_var, value="parquet").pack(side=tk.LEFT, padx=5)
        
        # Split data option
        ttk.Checkbutton(self.output_tab, text="Split into Train/Validation/Test Sets", 
                         variable=self.split_data_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # ------ Execution Tab ------
        # Status and progress
        ttk.Label(self.execution_tab, text="Status:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(self.execution_tab, textvariable=self.status_var).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(self.execution_tab, text="Progress:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.progress_bar = ttk.Progressbar(self.execution_tab, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=1, padx=10, pady=5, sticky="we")
        
        # Log display
        ttk.Label(self.execution_tab, text="Log:").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        self.log_text = tk.Text(self.execution_tab, height=15, width=70)
        self.log_text.grid(row=2, column=1, padx=10, pady=5)
        
        log_scroll = ttk.Scrollbar(self.execution_tab, command=self.log_text.yview)
        log_scroll.grid(row=2, column=2, sticky="ns", pady=5)
        self.log_text.config(yscrollcommand=log_scroll.set)
        
        # Run button
        self.run_btn = ttk.Button(self.execution_tab, text="Run ETL Process", command=self.run_etl, state="disabled")
        self.run_btn.grid(row=3, column=1, padx=10, pady=10)
        
        # Buttons for output management
        button_frame = ttk.Frame(self.execution_tab)
        button_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        ttk.Button(button_frame, text="Open Output Folder", 
                  command=lambda: os.startfile(self.output_dir_var.get())).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="View Output File", 
                  command=lambda: self._display_last_output_file()).pack(side=tk.LEFT, padx=5)
    
    def _setup_layout(self):
        """Set up the main layout for the application."""
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights to make the layout expandable
        for tab in [self.connection_tab, self.data_tab, self.output_tab, self.execution_tab]:
            tab.columnconfigure(1, weight=1)
        
        # Status bar at the bottom
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
    
    def _toggle_geo_options(self):
        """Show or hide geospatial options based on checkbox state."""
        if self.use_geo_var.get():
            self.geo_frame.grid()
        else:
            self.geo_frame.grid_remove()
    
    def log_message(self, message):
        """Add a message to the log text widget."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        logger.info(message)
    
    def connect_to_mongodb(self):
        """Connect to MongoDB and fetch databases and collections."""
        uri = self.uri_var.get()
        
        try:
            # Create a temporary ETL object to test connection
            temp_etl = MongoDBETL("test", custom_config={"uri": uri})
            
            # Get list of databases
            dbs = temp_etl.client.list_database_names()
            
            # Update database dropdown
            self.db_combo['values'] = dbs
            if dbs:
                self.db_combo.current(0)
                self.db_var.set(dbs[0])
            
            # Close temporary connection
            temp_etl.close()
            
            self.log_message(f"Successfully connected to MongoDB at {uri}")
            self.status_var.set("Connected")
            
            # Enable collection selection
            self.collection_combo.config(state="readonly")
            self.preview_btn.config(state="normal")
            self.run_btn.config(state="normal")
            
            # Fetch collections for the selected database
            self.update_collections()
            
            # Move to the next tab
            self.notebook.select(1)
            
        except Exception as e:
            self.log_message(f"Connection error: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to MongoDB: {str(e)}")
    
    def update_collections(self):
        """Update the collections list based on the selected database."""
        db_name = self.db_var.get()
        uri = self.uri_var.get()
        
        try:
            # Create a temporary ETL object to get collections
            temp_etl = MongoDBETL("test", custom_config={"uri": uri, "database": db_name})
            
            # Get list of collections
            self.collections = temp_etl.client[db_name].list_collection_names()
            
            # Update collection dropdown
            self.collection_combo['values'] = self.collections
            if self.collections:
                self.collection_combo.current(0)
                self.selected_collection.set(self.collections[0])
            
            # Close temporary connection
            temp_etl.close()
            
            self.log_message(f"Found {len(self.collections)} collections in database '{db_name}'")
            
        except Exception as e:
            self.log_message(f"Error fetching collections: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to fetch collections: {str(e)}")
    
    def preview_data(self):
        """Show a preview of the selected data in a new window."""
        try:
            uri = self.uri_var.get()
            db_name = self.db_var.get()
            collection_name = self.selected_collection.get()
            
            # Create ETL object for preview
            etl = MongoDBETL(collection_name, custom_config={"uri": uri, "database": db_name})
            
            # Parse query filter if provided
            query_filter = {}
            if self.query_filter_var.get():
                try:
                    query_filter = json.loads(self.query_filter_var.get())
                except json.JSONDecodeError:
                    messagebox.showerror("Query Error", "Invalid JSON in query filter")
                    return
            
            # Get limit value
            try:
                limit = int(self.limit_var.get())
            except ValueError:
                limit = 0
            
            # Extract data
            if self.use_geo_var.get() and self.geo_field_var.get():
                # Use geospatial extractor
                geo_extractor = GeoSpatialExtractor(
                    collection_name=collection_name,
                    geo_field=self.geo_field_var.get(),
                    config={"uri": uri, "database": db_name}
                )
                cursor = geo_extractor.extract(query_filter)
            else:
                cursor = etl.extract(query_filter)
            
            # Limit the number of documents for preview
            preview_limit = min(10, limit if limit > 0 else 10)
            preview_data = list(cursor.limit(preview_limit))
            
            # Close connection
            etl.close()
            
            # Create preview window
            preview_window = tk.Toplevel(self)
            preview_window.title(f"Preview: {collection_name}")
            preview_window.geometry("800x500")
            
            # Create text widget for JSON display
            preview_text = tk.Text(preview_window, wrap=tk.WORD)
            preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(preview_text, command=preview_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            preview_text.config(yscrollcommand=scrollbar.set)
            
            # Format and display the data
            formatted_json = json.dumps(preview_data, indent=2, default=str)
            preview_text.insert(tk.END, formatted_json)
            
            # Show metadata
            metadata_label = ttk.Label(preview_window, 
                                      text=f"Showing {len(preview_data)} of {cursor.count()} documents")
            metadata_label.pack(pady=5)
            
            self.log_message(f"Previewed {len(preview_data)} documents from {collection_name}")
            
        except Exception as e:
            self.log_message(f"Preview error: {str(e)}")
            messagebox.showerror("Preview Error", f"Failed to preview data: {str(e)}")
    
    def browse_output_dir(self):
        """Open a dialog to select the output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
            self.log_message(f"Output directory set to: {directory}")
    
    def run_etl(self):
        """Run the ETL process in a separate thread to avoid freezing the UI."""
        # Disable the run button during execution
        self.run_btn.config(state="disabled")
        self.status_var.set("Running...")
        self.progress_var.set(0)
        
        # Start ETL process in a separate thread
        threading.Thread(target=self._execute_etl, daemon=True).start()
    
    def _execute_etl(self):
        """Execute the ETL process based on user selections."""
        try:
            # Get parameters from UI
            uri = self.uri_var.get()
            db_name = self.db_var.get()
            collection_name = self.selected_collection.get()
            output_dir = self.output_dir_var.get()
            output_format = self.output_format_var.get()
            split_data = self.split_data_var.get()
            
            # Parse query filter if provided
            query_filter = {}
            if self.query_filter_var.get():
                try:
                    query_filter = json.loads(self.query_filter_var.get())
                except json.JSONDecodeError:
                    self.log_message("Error: Invalid JSON in query filter")
                    messagebox.showerror("Query Error", "Invalid JSON in query filter")
                    self.run_btn.config(state="normal")
                    self.status_var.set("Ready")
                    return
            
            # Get limit value
            try:
                limit = int(self.limit_var.get())
            except ValueError:
                limit = 0
            
            # Initialize ETL components
            self.log_message(f"Initializing ETL process for collection: {collection_name}")
            
            if self.use_geo_var.get() and self.geo_field_var.get():
                # Use geospatial extractor
                self.log_message(f"Using geospatial extractor with field: {self.geo_field_var.get()}")
                # Handle GeoSpatialExtractor initialization according to its signature
                etl = GeoSpatialExtractor(
                    collection_name=collection_name,
                    geo_field=self.geo_field_var.get(),
                    custom_config={"uri": uri, "database": db_name}
                )
            else:
                etl = MongoDBETL(
                    collection_name=collection_name,
                    custom_config={"uri": uri, "database": db_name}
                )
            
            # Initialize transformer and loader
            transformer = DataTransformer()
            loader = DataLoader(output_dir)
            
            # Extract data
            self.log_message("Extracting data...")
            self.progress_var.set(20)
            cursor = etl.extract(query_filter)
            
            if limit > 0:
                cursor = cursor.limit(limit)
                self.log_message(f"Limited extraction to {limit} documents")
            
            # Process the data
            self.log_message("Transforming data...")
            self.progress_var.set(40)
            
            # Define transformation function
            def transform_func(docs):
                try:
                    return transformer.transform_documents(docs)
                except Exception as e:
                    self.log_message(f"Transform error: {str(e)}")
                    return docs  # Return original docs if transformation fails
            
            # Define load function based on output format
            def load_func(transformed_docs):
                try:
                    filename = f"{collection_name}_export"
                    
                    if output_format == "json":
                        return loader.save_to_json(transformed_docs, filename)
                    elif output_format == "csv":
                        return loader.save_to_csv(transformed_docs, filename)
                    elif output_format == "parquet":
                        return loader.save_to_parquet(transformed_docs, filename)
                except Exception as e:
                    self.log_message(f"Load error: {str(e)}")
                    return None
            
            # Process the data
            self.log_message("Processing data in batches...")
            self.progress_var.set(60)
            
            # Process data - using batch_size from ETL object
            batch_count = 0
            doc_count = 0
            
            for batch in etl.get_batches(cursor):
                transformed_batch = transform_func(batch)
                load_func(transformed_batch)
                batch_count += 1
                doc_count += len(batch)
                
                # Update progress
                progress = 60 + (min(batch_count, 10) / 10) * 30
                self.progress_var.set(progress)
                self.log_message(f"Processed batch {batch_count} ({doc_count} documents)")
            
            stats = {
                "docs_processed": doc_count,
                "batch_count": batch_count
            }
            
            # If split option is selected, split the data
            if split_data:
                self.log_message("Splitting data into train/validation/test sets...")
                self.progress_var.set(90)
                
                # Get all transformed data
                all_data = []
                cursor = etl.extract(query_filter)
                if limit > 0:
                    cursor = cursor.limit(limit)
                
                for batch in etl.get_batches(cursor, 1000):
                    all_data.extend(transform_func(batch))
                
                # Split and save
                split_result = loader.split_and_save(
                    all_data,
                    f"{collection_name}_split",
                    format=output_format,
                    train_ratio=0.7,
                    val_ratio=0.15,
                    test_ratio=0.15
                )
                
                self.log_message(f"Split data saved to: {', '.join(split_result.values())}")
            
            # Complete
            self.progress_var.set(100)
            self.log_message(f"ETL process complete! Processed {stats['docs_processed']} documents.")
            self.log_message(f"Output saved to: {output_dir}")
            self.status_var.set("Completed")
            
            # Close connection
            etl.close()
            
            # Show completion message
            messagebox.showinfo("ETL Complete", f"Successfully processed {stats['docs_processed']} documents.")
            
            # Display the output file
            self._display_output_file(output_format, collection_name)
            
        except Exception as e:
            self.log_message(f"ETL error: {str(e)}")
            messagebox.showerror("ETL Error", f"Failed to process data: {str(e)}")
            self.status_var.set("Error")
        
        finally:
            # Re-enable run button
            self.run_btn.config(state="normal")

    def _display_output_file(self, output_format, collection_name):
        """Display the output file in the output viewer tab."""
        try:
            # Determine file path based on format
            output_dir = self.output_dir_var.get()
            filename = f"{collection_name}_export"
            
            if output_format == "json":
                file_path = os.path.join(output_dir, f"{filename}.json")
            elif output_format == "csv":
                file_path = os.path.join(output_dir, f"{filename}.csv")
            elif output_format == "parquet":
                file_path = os.path.join(output_dir, f"{filename}.parquet")
            else:
                self.log_message(f"Unknown output format: {output_format}")
                return
            
            # Store for later access
            self.last_output_file = file_path
            self.last_output_format = output_format
            
            # Display the file
            self._show_file_in_viewer(file_path, output_format)
            
            # Switch to the output viewer tab
            self.notebook.select(self.output_viewer_tab)
            
            self.log_message(f"Displayed output file: {file_path}")
            
        except Exception as e:
            self.log_message(f"Error displaying output file: {str(e)}")
    
    def _display_last_output_file(self):
        """Display the last output file that was generated."""
        if self.last_output_file and os.path.exists(self.last_output_file):
            self._show_file_in_viewer(self.last_output_file, self.last_output_format)
            self.notebook.select(self.output_viewer_tab)  # Switch to output viewer tab
        else:
            messagebox.showinfo("No Output File", "No output file has been generated yet.")
    
    def _show_file_in_viewer(self, file_path, file_format):
        """Display a file in the output viewer based on its format."""
        try:
            # Clear previous content safely
            for widget in list(self.output_viewer_frame.winfo_children()):
                try:
                    widget.destroy()
                except tk.TclError:
                    # Widget already destroyed, continue
                    pass
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_label = ttk.Label(self.output_viewer_frame, 
                                       text=f"File not found: {os.path.basename(file_path)}", 
                                       foreground="red")
                error_label.pack(padx=20, pady=20)
                return
            
            # Create header with file info
            header_frame = ttk.Frame(self.output_viewer_frame)
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(header_frame, text=f"File: {os.path.basename(file_path)}",
                     font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            
            ttk.Label(header_frame, text=f"Format: {file_format.upper()}").pack(side=tk.LEFT, padx=20)
            
            ttk.Button(header_frame, text="Refresh", 
                      command=lambda: self._show_file_in_viewer(file_path, file_format)).pack(side=tk.RIGHT, padx=5)
            
            # Create content viewer with scrollbars
            content_frame = ttk.Frame(self.output_viewer_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Configure grid layout for proper scrollbar positioning
            content_frame.grid_rowconfigure(0, weight=1)
            content_frame.grid_columnconfigure(0, weight=1)
            
            # Create text widget for viewing content
            content_view = tk.Text(content_frame, wrap=tk.NONE)
            content_view.grid(row=0, column=0, sticky="nsew")
            
            # Add vertical scrollbar
            v_scroll = ttk.Scrollbar(content_frame, orient="vertical")
            v_scroll.grid(row=0, column=1, sticky="ns")
            
            # Add horizontal scrollbar
            h_scroll = ttk.Scrollbar(content_frame, orient="horizontal")
            h_scroll.grid(row=1, column=0, sticky="ew")
            
            # Connect scrollbars to text widget
            content_view.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            v_scroll.config(command=content_view.yview)
            h_scroll.config(command=content_view.xview)
            
            # Load and display file content based on format
            try:
                if file_format == "json":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            # Try to load and pretty-print JSON
                            data = json.load(f)
                            content = json.dumps(data, indent=2, default=str)
                        except json.JSONDecodeError:
                            # If that fails, just show the raw file
                            f.seek(0)
                            content = f.read()
                    
                    content_view.insert(tk.END, content)
                    
                elif file_format == "csv":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content_view.insert(tk.END, content)
                    
                elif file_format == "parquet":
                    try:
                        # Use pandas to read parquet and display as text
                        import pandas as pd
                        df = pd.read_parquet(file_path)
                        content_view.insert(tk.END, df.to_string())
                    except Exception as e:
                        content_view.insert(tk.END, f"Unable to display Parquet file: {str(e)}\n\n"
                                                  f"Parquet files are binary and require pandas to view.")
                
                # Make text widget read-only
                content_view.config(state="disabled")
                
                # Add status bar with file info
                status_frame = ttk.Frame(self.output_viewer_frame)
                status_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Show file size
                file_size = os.path.getsize(file_path)
                size_text = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"
                
                ttk.Label(status_frame, text=f"Size: {size_text}").pack(side=tk.LEFT)
                
                # Add timestamp
                mod_time = os.path.getmtime(file_path)
                import datetime
                timestamp = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                ttk.Label(status_frame, text=f"Last Modified: {timestamp}").pack(side=tk.RIGHT)
                
            except Exception as file_error:
                content_view.insert(tk.END, f"Error reading file: {str(file_error)}")
                content_view.config(state="disabled")
            
        except Exception as e:
            # Create a simple error message if viewing fails
            try:
                for widget in list(self.output_viewer_frame.winfo_children()):
                    try:
                        widget.destroy()
                    except tk.TclError:
                        pass
            except:
                pass
                
            error_label = ttk.Label(self.output_viewer_frame, 
                                   text=f"Error displaying file: {str(e)}", 
                                   foreground="red")
            error_label.pack(padx=20, pady=20)
            
            self.log_message(f"Error in file viewer: {str(e)}")

def main():
    """Main entry point for the GUI application."""
    app = MongoDBETLApp()
    app.mainloop()

if __name__ == "__main__":
    main()
