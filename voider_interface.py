import os
import sys
import tkinter as tk
from tkinter import messagebox, Canvas, Entry, font
import random
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VoiderInterface:
    def __init__(self, root, void_dir):
        self.root = root
        self.void_dir = void_dir
        self.void_file_path = os.path.join(void_dir, '0.txt')

        self.root.title("Voider")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 1)  

        self.opacity = 1.0

        # Hide the mouse cursor
        self.root.config(cursor="none")

        # Bind focus in event to ensure the Entry widget is always focused
        self.root.bind('<FocusIn>', self.on_focus_in)

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Subtract margin for aesthetics
        thickness = 10

        # Create a canvas widget with no border
        self.canvas = Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Calculate circle center coordinates
        center_x = screen_width // 2
        center_y = screen_height // 2

        # Create the white circle outline
        radius = min(screen_width, screen_height) // 2 - thickness - 25
        self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="white", width=thickness)

        # Calculate the circle's diameter
        diameter = 2 * radius

        # Create an invisible Entry widget in the middle of the screen
        entry_font = font.Font(family="Consolas", size=11)

        # Estimate the average character width using the font metrics
        average_char_width = entry_font.measure("0")

        # Calculate the entry width in characters based on the circle's diameter
        entry_width = (diameter - 20) // average_char_width

        self.entry = Entry(self.root, borderwidth=0, highlightthickness=0, bg="black", fg="white", justify="center", font=entry_font, width=entry_width, insertbackground="white")
        self.entry.place(x=center_x, y=center_y, anchor="center")

        # Set focus to the Entry widget to ensure the cursor is blinking
        self.entry.focus_set()
        
        self.entry.unbind('<Control-x>')
        self.entry.unbind('<Control-z>')

        # Bind necessary events
        self.entry.bind('<space>', self.void_line)  # Bind Enter key to void_line method
        # self.entry.bind('<Key>', self.hide_cursor)  
        self.root.bind('<Motion>', self.show_cursor)  # Bind mouse motion to show the cursor
        self.root.bind('<MouseWheel>', self.on_mouse_scroll) # Bind mouse wheel to on_mouse_scroll method
        self.root.bind('<Return>', self.on_key_press)  # Right Alt (Alt Gr) key  
        self.root.bind('<BackSpace>', self.close_program)  # Right Alt (Alt Gr) key  
        self.root.bind('<Up>', self.increase_opacity)
        self.root.bind('<Down>', self.decrease_opacity)

        self.canvas.configure(bg="black")

        self.current_line = None
        self.all_lines = []  # List to store all lines from all .txt files

        self.update_txt_files()  # Update txt_files based on current state

        # Start indexing lines in a separate thread
        self.indexing_thread = threading.Thread(target=self.index_all_lines)
        self.indexing_thread.start()

        # Set up file system watcher
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_modified = self.on_directory_change
        self.event_handler.on_created = self.on_directory_change
        self.event_handler.on_deleted = self.on_directory_change
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.void_dir, recursive=False)
        self.observer.start()

    def set_opacity(self):
        # Ensure opacity stays within the range [0.0, 1.0]
        self.opacity = max(0.0, min(1.0, self.opacity))
        self.root.attributes("-alpha", self.opacity)

    def increase_opacity(self, event=None):
        if self.opacity < 1.0:  # Cap at 1.0
            self.opacity = min(1.0, self.opacity + 0.1)  # Increment but don't exceed 1.0
            self.set_opacity()

    def decrease_opacity(self, event=None):
        if self.opacity > 0.0:  # Cap at 0.0
            self.opacity = max(0.0, self.opacity - 0.1)  # Decrement but don't go below 0.0
            self.set_opacity()

    def close_program(self, event=None):
        self.root.destroy()

    def on_focus_in(self, event):
        self.entry.focus_set()

    def hide_cursor(self, event=None):
        self.entry.config(insertbackground="black")

    def show_cursor(self, event=None):
        self.entry.config(insertbackground="white")

    def update_txt_files(self):
        # Ensure the void directory exists
        if not os.path.exists(self.void_dir):
            os.makedirs(self.void_dir)

        # Ensure the 0.txt file exists
        if not os.path.exists(self.void_file_path):
            with open(self.void_file_path, 'w', encoding='utf-8') as void_file:
                void_file.write('')

        # Exclude '0.txt' when listing files
        self.txt_files = [f for f in os.listdir(self.void_dir) if f.endswith('.txt') and f != '0.txt']

    def index_all_lines(self):
        # Read and store all lines from all .txt files
        self.all_lines = []  # Reset list
        for txt_file in self.txt_files:
            file_path = os.path.join(self.void_dir, txt_file)
            if os.path.exists(file_path):  # Check if the file still exists
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    self.all_lines.extend([line.strip() for line in lines if line.strip()])

    def on_directory_change(self, event):
        # Update the file list and reindex lines on directory change
        self.update_txt_files()
        self.indexing_thread = threading.Thread(target=self.index_all_lines)
        self.indexing_thread.start()

    def on_key_press(self, event):
        if event.keysym == 'Return':
            self.show_random_line()
            return 'break'
        self.hide_cursor(event)

    def on_mouse_scroll(self, event):
        if event.delta < 0:  # Scrolling down
            self.show_random_line()

    def show_random_line(self):
        if self.indexing_thread.is_alive():
            messagebox.showinfo("Indexing", "Please wait, indexing lines...")
            return

        valid_lines = [line for line in self.all_lines if line.strip() != '.']

        if valid_lines:
            self.current_line = random.choice(valid_lines)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, self.current_line)

            self.hide_cursor(None)  # Hide the cursor after inserting the line
        else:
            self.update_txt_files()
            self.indexing_thread = threading.Thread(target=self.index_all_lines)
            self.indexing_thread.start()
            messagebox.showinfo("nothing found", "nothing found in the void")

    def void_line(self, event=None):
        line = self.entry.get().strip()
        if line:
            # Check if the line starts with "0"
            if line.startswith("0"):
                base, ext = os.path.splitext(self.void_file_path)
                if line == "0":
                    # Generate a random number with a random number of digits
                    num_digits = random.randint(1, 10)
                    random_number = ''.join([str(random.randint(0, 9)) for _ in range(num_digits)])
                    new_file_path = f"{base}_{random_number}{ext}"
                else:
                    # Use the rest of the line after "0" as the new name
                    new_name = line[1:]
                    new_file_path = os.path.join(self.void_dir, f"{new_name}{ext}")
                
                # Check if the new file already exists
                if os.path.exists(new_file_path):
                    # If the file exists, append the content of '0.txt' into it
                    with open(self.void_file_path, 'r', encoding='utf-8') as void_file:
                        content_to_append = void_file.read()
                    with open(new_file_path, 'a', encoding='utf-8') as target_file:
                        target_file.write(content_to_append)
                    # Clear '0.txt' after appending its content
                    with open(self.void_file_path, 'w', encoding='utf-8') as void_file:
                        void_file.write('')
                else:
                    # If the file doesn't exist, rename '0.txt' to the new file name
                    os.rename(self.void_file_path, new_file_path)
                    # Create a new '0.txt' file
                    with open(self.void_file_path, 'w', encoding='utf-8') as void_file:
                        void_file.write('')
            else:
                # Regular input case: Split by dots, add the dot as a separate line
                segments = []
                for part in line.split('.'):
                    if part.strip():
                        segments.append(part.strip())  # Add non-empty segments
                    segments.append('.')  # Add the dot as its own line
                
                # Remove trailing dot if it exists
                if segments and segments[-1] == '.':
                    segments.pop()
                
                # Write each formatted line to the file
                if segments:  # Ensure there are valid lines to write
                    with open(self.void_file_path, 'a', encoding='utf-8') as void_file:
                        void_file.write('\n'.join(segments) + '\n')
                        void_file.flush()
                        os.fsync(void_file.fileno())

            # Clear the entry field for the next input
            self.entry.delete(0, tk.END)
            self.entry.focus_set()
            self.show_cursor()  # Show the cursor again

        return 'break'


    def delete_except_highlighted(self, event=None):
        try:
            selected_text = self.entry.selection_get()  # Get the highlighted text
            if selected_text:
                # Get the start and end indices of the selection
                start_index = self.entry.index(tk.SEL_FIRST)
                end_index = self.entry.index(tk.SEL_LAST)
                
                # Delete everything except the selected text
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, selected_text)
                
                # Restore the selection
                self.entry.tag_add(tk.SEL, start_index, end_index)
            else:
                messagebox.showwarning("Warning", "No text is selected to keep.")
        except tk.TclError:
            messagebox.showwarning("Warning", "No text selected.")

# Main application entry point
if __name__ == "__main__":
    if getattr(sys, 'frozen', False):  # Check if running as a bundled exe
        app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.path.dirname(__file__)

    void_dir = os.path.join(app_path, 'void')
    root = tk.Tk()
    app = VoiderInterface(root, void_dir)
    root.mainloop()