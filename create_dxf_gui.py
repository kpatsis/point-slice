#!/usr/bin/env python3

"""
DXF Document Creator - GUI Version

A graphical user interface for creating DXF files from CSV point cloud data.
Provides the same functionality as the command line version with an intuitive GUI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import List, Optional
import io
import contextlib

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the main functionality
from create_dxf import create_dxf_from_csv_directory


class RedirectText:
    """Helper class to redirect print output to a text widget."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.update()
    
    def flush(self):
        pass


class DXFCreatorGUI:
    """Main GUI application for DXF creation."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DXF Document Creator")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        # Variables for form inputs
        self.input_directory = tk.StringVar(value="tests/testdata/02_csv")
        self.output_file = tk.StringVar(value="output.dxf")
        self.colors_text = tk.StringVar(value="1 2 3 4 5 6 7 8 9 10")
        self.label_x = tk.DoubleVar(value=-40.0)
        self.label_y = tk.DoubleVar(value=0.0)
        
        self.processing = False
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="DXF Document Creator", 
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1
        
        # Input Directory Section
        ttk.Label(main_frame, text="Input Directory:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_directory, width=50)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_directory).grid(row=0, column=1)
        row += 1
        
        # Output File Section
        ttk.Label(main_frame, text="Output File:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_file, width=50)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(output_frame, text="Save As...", command=self.browse_output_file).grid(row=0, column=1)
        row += 1
        
        # Colors Section
        ttk.Label(main_frame, text="Colors (1-256):").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        colors_frame = ttk.Frame(main_frame)
        colors_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        colors_frame.columnconfigure(0, weight=1)
        
        self.colors_entry = ttk.Entry(colors_frame, textvariable=self.colors_text, width=50)
        self.colors_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(colors_frame, text="Reset", command=self.reset_colors).grid(row=0, column=1)
        
        # Help text for colors
        ttk.Label(
            main_frame, 
            text="Enter space-separated color numbers (e.g., '1 2 3 4 5')", 
            font=("TkDefaultFont", 8),
            foreground="gray"
        ).grid(row=row+1, column=1, columnspan=2, sticky=tk.W)
        row += 2
        
        # Label Position Section
        label_frame = ttk.LabelFrame(main_frame, text="Label Position", padding="5")
        label_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        label_frame.columnconfigure(1, weight=1)
        label_frame.columnconfigure(3, weight=1)
        
        ttk.Label(label_frame, text="X:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.label_x_entry = ttk.Entry(label_frame, textvariable=self.label_x, width=15)
        self.label_x_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(label_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.label_y_entry = ttk.Entry(label_frame, textvariable=self.label_y, width=15)
        self.label_y_entry.grid(row=0, column=3, sticky=tk.W)
        
        row += 1
        
        # Process Button
        self.process_button = ttk.Button(
            main_frame, 
            text="Create DXF File", 
            command=self.process_files,
            style="Accent.TButton"
        )
        self.process_button.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1
        
        # Progress/Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Progress & Log", padding="5")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear Log Button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, pady=(5, 0))
        
        # Initial log message
        self.log_text.insert(tk.END, "Ready to create DXF files from CSV point cloud data.\n")
        self.log_text.insert(tk.END, "Configure your settings above and click 'Create DXF File' to begin.\n\n")
    
    def browse_input_directory(self):
        """Open directory selection dialog for input directory."""
        directory = filedialog.askdirectory(
            title="Select Directory Containing CSV Files",
            initialdir=self.input_directory.get() if os.path.exists(self.input_directory.get()) else "."
        )
        if directory:
            self.input_directory.set(directory)
    
    def browse_output_file(self):
        """Open file save dialog for output file."""
        filename = filedialog.asksaveasfilename(
            title="Save DXF File As",
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")],
            initialfile=self.output_file.get()
        )
        if filename:
            self.output_file.set(filename)
    
    def reset_colors(self):
        """Reset colors to default values."""
        self.colors_text.set("1 2 3 4 5 6 7 8 9 10")
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete(1.0, tk.END)
    
    def validate_inputs(self) -> bool:
        """Validate all input fields before processing."""
        
        # Check input directory
        if not os.path.exists(self.input_directory.get()):
            messagebox.showerror("Error", f"Input directory does not exist:\n{self.input_directory.get()}")
            return False
        
        if not os.path.isdir(self.input_directory.get()):
            messagebox.showerror("Error", f"Input path is not a directory:\n{self.input_directory.get()}")
            return False
        
        # Check output file directory
        output_dir = os.path.dirname(os.path.abspath(self.output_file.get()))
        if not os.path.exists(output_dir):
            messagebox.showerror("Error", f"Output directory does not exist:\n{output_dir}")
            return False
        
        # Validate colors
        colors_str = self.colors_text.get().strip()
        if colors_str:
            try:
                colors = [int(c) for c in colors_str.split()]
                invalid_colors = [c for c in colors if c < 1 or c > 256]
                if invalid_colors:
                    messagebox.showerror("Error", f"Invalid color indices: {invalid_colors}\nColors must be between 1-256.")
                    return False
            except ValueError:
                messagebox.showerror("Error", "Colors must be space-separated integers (e.g., '1 2 3 4 5')")
                return False
        
        return True
    
    def parse_colors(self) -> Optional[List[int]]:
        """Parse colors from the text input."""
        colors_str = self.colors_text.get().strip()
        if not colors_str:
            return None
        
        try:
            return [int(c) for c in colors_str.split()]
        except ValueError:
            return None
    
    def process_files(self):
        """Process the files in a separate thread to avoid blocking the GUI."""
        if self.processing:
            return
        
        if not self.validate_inputs():
            return
        
        self.processing = True
        self.process_button.config(text="Processing...", state="disabled")
        self.clear_log()
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.run_processing, daemon=True)
        thread.start()
    
    def run_processing(self):
        """Run the actual processing in a background thread."""
        try:
            # Redirect stdout to the log widget
            old_stdout = sys.stdout
            sys.stdout = RedirectText(self.log_text)
            
            # Get parameters
            input_dir = self.input_directory.get()
            output_file = self.output_file.get()
            colors = self.parse_colors()
            label_position = (self.label_x.get(), self.label_y.get())
            
            # Run the processing
            create_dxf_from_csv_directory(
                input_dir,
                output_file,
                colors,
                label_position
            )
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"DXF file created successfully!\n\nOutput: {output_file}"
            ))
            
        except Exception as e:
            # Show error message
            error_msg = f"An error occurred during processing:\n\n{str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            print(f"\n❌ Error: {str(e)}")
            
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            
            # Re-enable the button
            self.root.after(0, self.processing_completed)
    
    def processing_completed(self):
        """Called when processing is completed."""
        self.processing = False
        self.process_button.config(text="Create DXF File", state="normal")


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    
    # Set up the style for better appearance
    style = ttk.Style()
    
    # Try to use a modern theme if available
    available_themes = style.theme_names()
    if "vista" in available_themes:
        style.theme_use("vista")
    elif "clam" in available_themes:
        style.theme_use("clam")
    
    app = DXFCreatorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")


if __name__ == "__main__":
    main() 