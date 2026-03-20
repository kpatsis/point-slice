#!/usr/bin/env python3

# Point Slice Studio - Convert CSV point cloud data to DXF format
# Copyright (C) 2024 [Your Name]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Point Slice Studio - GUI Version

A graphical user interface for creating DXF files from CSV point cloud data.
Provides the same functionality as the command line version with an intuitive GUI.
"""

import os
import queue
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import List, Optional

from ps_core.workflow import create_dxf_from_csv_directory

_POLL_INTERVAL_MS = 50


class RedirectText:
    """Redirect print output to a tkinter text widget in a thread-safe way.

    Strings written from any thread are placed into a queue.  The main
    thread drains the queue on a timer and performs the actual widget
    updates, which keeps all tkinter calls on the correct thread.
    """

    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.text_widget = text_widget
        self._queue: queue.Queue[str] = queue.Queue()
        self._polling = False
        self._after_id: Optional[str] = None

    def start_polling(self):
        """Begin draining the queue on the main-thread event loop.

        Must be called from the main thread.  tkinter widget methods
        (including ``after()``) are not thread-safe.
        """
        if not self._polling:
            self._polling = True
            self._after_id = self.text_widget.after(0, self._poll)

    def stop_polling(self):
        """Stop the polling timer and drain any remaining output.

        Must be called from the main thread.  Cancels any scheduled
        ``_poll()`` callback and performs a final synchronous drain
        to avoid leftover text appearing in a subsequent run.
        """
        self._polling = False
        if self._after_id is not None:
            self.text_widget.after_cancel(self._after_id)
            self._after_id = None
        self._drain()

    def write(self, string: str):
        self._queue.put(string)

    def flush(self):
        pass

    def _poll(self):
        self._drain()
        if self._polling:
            self._after_id = self.text_widget.after(_POLL_INTERVAL_MS, self._poll)

    def _drain(self):
        """Drain queued text with a single insert per poll to keep UI responsive."""
        chunks: List[str] = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if chunks:
            self.text_widget.insert(tk.END, "".join(chunks))
            self.text_widget.see(tk.END)


class PointSliceStudioGUI:
    """Main GUI application for DXF creation."""

    def __init__(self, root):
        self.root = root
        self.root.title("Point Slice Studio")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Set the window icon using the same icon as the application
        try:
            # Handle both development and packaged application scenarios
            if getattr(sys, "frozen", False):
                # Running as packaged application - use PyInstaller's temp directory
                application_path = getattr(
                    sys, "_MEIPASS", os.path.dirname(sys.executable)
                )
                icon_path = os.path.join(application_path, "point_slice_studio.ico")
            else:
                # Running as script
                icon_path = os.path.join(
                    os.path.dirname(__file__), "point_slice_studio.ico"
                )

            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # If it fails, use the default system icon

        # Variables for form inputs
        self.input_directory = tk.StringVar(value="tests/testdata/02_csv")
        self.output_file = tk.StringVar(value="output.dxf")
        self.colors_text = tk.StringVar(value="1 2 3 4 5 6 7 8 9 10")
        self.label_x = tk.DoubleVar(value=-40.0)
        self.label_y = tk.DoubleVar(value=0.0)
        self.anchor_x = tk.DoubleVar(value=0.0)
        self.anchor_y = tk.DoubleVar(value=0.0)
        self.xz_rotated_x_offset = tk.DoubleVar(value=-300.0)
        self.yz_rotated_x_offset = tk.DoubleVar(value=-200.0)

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
            main_frame, text="Point Slice Studio", font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1

        # Input Directory Section
        ttk.Label(main_frame, text="Input Directory:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )

        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_entry = ttk.Entry(
            input_frame, textvariable=self.input_directory, width=50
        )
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            input_frame, text="Browse...", command=self.browse_input_directory
        ).grid(row=0, column=1)
        row += 1

        # Output File Section
        ttk.Label(main_frame, text="Output File:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )

        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)

        self.output_entry = ttk.Entry(
            output_frame, textvariable=self.output_file, width=50
        )
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            output_frame, text="Save As...", command=self.browse_output_file
        ).grid(row=0, column=1)
        row += 1

        # Colors Section
        ttk.Label(main_frame, text="Colors (1-256):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )

        colors_frame = ttk.Frame(main_frame)
        colors_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        colors_frame.columnconfigure(0, weight=1)

        self.colors_entry = ttk.Entry(
            colors_frame, textvariable=self.colors_text, width=50
        )
        self.colors_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(colors_frame, text="Reset", command=self.reset_colors).grid(
            row=0, column=1
        )

        # Help text for colors
        ttk.Label(
            main_frame,
            text="Enter space-separated color numbers (e.g., '1 2 3 4 5')",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).grid(row=row + 1, column=1, columnspan=2, sticky=tk.W)
        row += 2

        # Label Position Section
        label_wrapper = ttk.Frame(main_frame)
        label_wrapper.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)
        label_frame = ttk.LabelFrame(label_wrapper, text="Label Position", padding="5")
        label_frame.pack(anchor=tk.W)

        label_inner = ttk.Frame(label_frame)
        label_inner.pack(anchor=tk.W)
        ttk.Label(label_inner, text="X:").pack(side=tk.LEFT, padx=(0, 2))
        self.label_x_entry = ttk.Entry(label_inner, textvariable=self.label_x, width=12)
        self.label_x_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(label_inner, text="Y:").pack(side=tk.LEFT, padx=(0, 2))
        self.label_y_entry = ttk.Entry(label_inner, textvariable=self.label_y, width=12)
        self.label_y_entry.pack(side=tk.LEFT)

        row += 1

        # Anchor point and rotated-slice offsets (separate groups)
        layout_wrapper = ttk.Frame(main_frame)
        layout_wrapper.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)

        anchor_frame = ttk.LabelFrame(layout_wrapper, text="Anchor point", padding="5")
        anchor_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 8))
        anchor_inner = ttk.Frame(anchor_frame)
        anchor_inner.pack(anchor=tk.W)
        ttk.Label(anchor_inner, text="X:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(anchor_inner, textvariable=self.anchor_x, width=12).pack(
            side=tk.LEFT, padx=(0, 12)
        )
        ttk.Label(anchor_inner, text="Y:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(anchor_inner, textvariable=self.anchor_y, width=12).pack(side=tk.LEFT)
        ttk.Label(
            anchor_frame,
            text="Base (x, y) of the imported point cloud (CLI: --anchor-x / --anchor-y).",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(6, 0))

        offsets_frame = ttk.LabelFrame(
            layout_wrapper, text="Rotated slice offsets", padding="5"
        )
        offsets_frame.pack(anchor=tk.W, fill=tk.X)
        offsets_inner = ttk.Frame(offsets_frame)
        offsets_inner.pack(anchor=tk.W)
        ttk.Label(offsets_inner, text="XZ-slice X offset:").pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Entry(offsets_inner, textvariable=self.xz_rotated_x_offset, width=12).pack(
            side=tk.LEFT, padx=(0, 12)
        )
        ttk.Label(offsets_inner, text="YZ-slice X offset:").pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Entry(offsets_inner, textvariable=self.yz_rotated_x_offset, width=12).pack(
            side=tk.LEFT
        )
        ttk.Label(
            offsets_frame,
            text=(
                "Added to anchor X for each rotated slice type "
                "(CLI: --xz-rotated-x-offset / --yz-rotated-x-offset)."
            ),
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(6, 0))

        row += 1

        # Process Button
        self.process_button = ttk.Button(
            main_frame,
            text="Create DXF File",
            command=self.process_files,
            style="Accent.TButton",
        )
        self.process_button.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

        # Progress/Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Progress & Log", padding="5")
        log_frame.grid(
            row=row,
            column=0,
            columnspan=3,
            sticky=(tk.W, tk.E, tk.N, tk.S),
            pady=(10, 0),
        )
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Clear Log Button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(
            row=1, column=0, pady=(5, 0)
        )

        # Initial log message
        self.log_text.insert(
            tk.END, "Ready to create DXF files from CSV point cloud data.\n"
        )
        self.log_text.insert(
            tk.END,
            "Configure your settings above and click 'Create DXF File' to begin.\n\n",
        )

    def browse_input_directory(self):
        """Open directory selection dialog for input directory."""
        directory = filedialog.askdirectory(
            title="Select Directory Containing CSV Files",
            initialdir=(
                self.input_directory.get()
                if os.path.exists(self.input_directory.get())
                else "."
            ),
        )
        if directory:
            self.input_directory.set(directory)

    def browse_output_file(self):
        """Open file save dialog for output file."""
        filename = filedialog.asksaveasfilename(
            title="Save DXF File As",
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")],
            initialfile=self.output_file.get(),
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
            messagebox.showerror(
                "Error",
                f"Input directory does not exist:\n{self.input_directory.get()}",
            )
            return False

        if not os.path.isdir(self.input_directory.get()):
            messagebox.showerror(
                "Error", f"Input path is not a directory:\n{self.input_directory.get()}"
            )
            return False

        # Check output file directory
        output_dir = os.path.dirname(os.path.abspath(self.output_file.get()))
        if not os.path.exists(output_dir):
            messagebox.showerror(
                "Error", f"Output directory does not exist:\n{output_dir}"
            )
            return False

        # Validate colors
        colors_str = self.colors_text.get().strip()
        if colors_str:
            try:
                colors = [int(c) for c in colors_str.split()]
                invalid_colors = [c for c in colors if c < 1 or c > 256]
                if invalid_colors:
                    messagebox.showerror(
                        "Error",
                        f"Invalid color indices: {invalid_colors}\nColors must be between 1-256.",
                    )
                    return False
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Colors must be space-separated integers (e.g., '1 2 3 4 5')",
                )
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

        input_dir = self.input_directory.get()
        output_file = self.output_file.get()
        colors = self.parse_colors()
        label_position = (self.label_x.get(), self.label_y.get())
        anchor_point = (self.anchor_x.get(), self.anchor_y.get())
        xz_off = self.xz_rotated_x_offset.get()
        yz_off = self.yz_rotated_x_offset.get()

        self._redirector = RedirectText(self.log_text)
        self._redirector.start_polling()

        self._old_stdout = sys.stdout
        sys.stdout = self._redirector

        thread = threading.Thread(
            target=self._run_processing,
            args=(
                input_dir,
                output_file,
                colors,
                label_position,
                anchor_point,
                xz_off,
                yz_off,
            ),
            daemon=True,
        )
        thread.start()

    def _run_processing(
        self,
        input_dir,
        output_file,
        colors,
        label_position,
        anchor_point,
        xz_rotated_x_offset,
        yz_rotated_x_offset,
    ):
        """Run the actual processing in a background thread.

        This method only calls ``create_dxf_from_csv_directory`` (which
        uses ``print``).  All tkinter interaction is handled by the main
        thread via ``after`` callbacks.
        """
        try:
            create_dxf_from_csv_directory(
                input_dir,
                output_file,
                anchor_point=anchor_point,
                xz_rotated_x_offset=xz_rotated_x_offset,
                yz_rotated_x_offset=yz_rotated_x_offset,
                colors=colors,
                label_position=label_position,
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"DXF file created successfully!\n\nOutput: {output_file}",
                ),
            )

        except Exception as e:
            error_msg = f"An error occurred during processing:\n\n{str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            print(f"\n❌ Error: {str(e)}")

        finally:
            self.root.after(0, self._finish_processing)

    def _finish_processing(self):
        """Called on the main thread when the worker is done."""
        sys.stdout = self._old_stdout
        self._redirector.stop_polling()
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

    PointSliceStudioGUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")


if __name__ == "__main__":
    main()
