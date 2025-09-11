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
from mongodb_etl.mongodb_etl import MongoDBETL
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader
from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
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
        
        # Create the main interface
        self._create_widgets()
        self._setup_layout()
        
        # Status variables
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
    
    def _create_widgets(self):
        """Create all the widgets for the application."""
        # Main notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        
        # Create tabs
        self.connection_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)
        self.execution_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.connection_tab, text="Connection")
        self.notebook.add(self.data_tab, text="Data Selection")
        self.notebook.add(self.output_tab, text="Output Settings")
        self.notebook.add(self.execution_tab, text="Run ETL")
        
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
        
        # Open output folder button
        ttk.Button(self.execution_tab, text="Open Output Folder", 
                    command=lambda: os.startfile(self.output_dir_var.get())).grid(row=3, column=0, padx=10, pady=10)
    
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
            temp_etl = MongoDBETL("test", {"uri": uri})
            
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
            temp_etl = MongoDBETL("test", {"uri": uri, "database": db_name})
            
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
            etl = MongoDBETL(collection_name, {"uri": uri, "database": db_name})
            
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
                etl = GeoSpatialExtractor(
                    collection_name=collection_name,
                    geo_field=self.geo_field_var.get(),
                    config={"uri": uri, "database": db_name}
                )
            else:
                etl = MongoDBETL(
                    collection_name=collection_name,
                    config={"uri": uri, "database": db_name}
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
                return transformer.transform_documents(docs)
            
            # Define load function based on output format
            def load_func(transformed_docs):
                filename = f"{collection_name}_export"
                
                if output_format == "json":
                    return loader.save_to_json(transformed_docs, filename)
                elif output_format == "csv":
                    return loader.save_to_csv(transformed_docs, filename)
                elif output_format == "parquet":
                    return loader.save_to_parquet(transformed_docs, filename)
            
            # Process the data
            self.log_message("Processing data in batches...")
            self.progress_var.set(60)
            
            # Set up a callback for progress updates
            def progress_callback(batch_num, total_docs, total_batches=None):
                if total_batches:
                    progress = 60 + (batch_num / total_batches) * 30
                    self.progress_var.set(progress)
                    self.log_message(f"Processed batch {batch_num}/{total_batches} ({total_docs} documents)")
            
            # Process data
            stats = etl.process_in_batches(
                cursor=cursor,
                transform_func=transform_func,
                load_func=load_func,
                batch_size=1000,
                progress_callback=progress_callback
            )
            
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
            
        except Exception as e:
            self.log_message(f"ETL error: {str(e)}")
            messagebox.showerror("ETL Error", f"Failed to process data: {str(e)}")
            self.status_var.set("Error")
        
        finally:
            # Re-enable run button
            self.run_btn.config(state="normal")

def main():
    """Main entry point for the GUI application."""
    app = MongoDBETLApp()
    app.mainloop()

if __name__ == "__main__":
    main()
