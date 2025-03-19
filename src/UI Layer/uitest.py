import tkinter as tk
from tkinter import ttk
import ctypes

import threading
import darkdetect #for system dark/light mode detection
import sv_ttk #windows 11 like theme

# Enable DPI awareness for better scaling on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    print(f"Failed to set DPI awareness: {e}")

#app inherits Tkinter
class App(tk.Tk):
    def __init__(self, windowTitle: str):
        super().__init__()

        self.initialize_main_window(windowTitle)
        
        self.initialize_theme()
        
        self.initialize_sidebar()

        # Minimum size to hold all buttons in the sidebar
        sidebar_width = 150
        button_height = 40
        padding = 10
        num_buttons = 2  # Only counting the top buttons now
        min_height = (button_height + padding) * num_buttons + padding
        self.minsize(sidebar_width + 200, min_height)

        # Sidebar Frame
        self.sidebar = tk.Frame(self, width=sidebar_width, height=min_height)
        self.sidebar.pack(side="left", fill="y")

        # Shadow Frame (simulates a shadow effect)
        self.shadow = tk.Frame(self, width=4, bg="#bdc3c7")  # Light gray for shadow effect
        self.shadow.pack(side="left", fill="y")

        # Sidebar Buttons (Top Buttons)
        self.btn1 = ttk.Button(self.sidebar, text="Button 1",
                               style="TButton",
                               takefocus=False,
                               command=lambda: self.show_message("Button 1 clicked"))
        self.btn1.pack(pady=(padding, 0), fill="x", padx=5)

        # Separator Below Button 1
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=(5, 5))

        self.btn2 = ttk.Button(self.sidebar, text="Button 2",
                               style="TButton",
                               takefocus=False,
                               command=lambda: self.show_message("Button 2 clicked"))
        self.btn2.pack(pady=(0, 0), fill="x", padx=5)

        # Separator Below Button 2
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=(5, 5))

        # Button Snapped to Bottom with Gear Emoji
        self.btn3 = ttk.Button(self.sidebar, text="⚙️",
                               style="TButton",
                               takefocus=False,
                               command=lambda: self.show_message("Settings clicked"))
        self.btn3.pack(side="bottom", pady=padding, fill="x", padx=5)

        # Main Content Area
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")

        self.label = tk.Label(self.content, text="Welcome!", font=("Arial", 24))
        self.label.pack(pady=20)

    def show_message(self, message):
        self.label.config(text=message)
        
    #function initialzies the main window and associated settings
    def initialize_main_window(self, windowTitle: str):
        self.title(windowTitle)
        self.geometry("600x400")
        
    #function will be called if the systemwide dark mode setting changes
    def darkmode_callback(self, theme):
        sv_ttk.set_theme(theme = theme, root = self)
        
    def initialize_theme(self):
        # Apply Native Windows Theme
        sv_ttk.set_theme(theme = darkdetect.theme(), root = self)
        
        # Ensure that the app will follow the system darkmode setting
        self.darkModeListener = threading.Thread(target=darkdetect.listener, args=(self.darkmode_callback,))
        self.darkModeListener.daemon = True
        self.darkModeListener.start()
        
    def initialize_sidebar(self):
        sidebar_width = int(self.winfo_fpixels('70p')) #sidebar width is 70 "points" -> 70 * 1/72 inch
        button_height = int(self.winfo_fpixels('40p')) #button height is 40 points
        button_padding = int(self.winfo_fpixels('10p')) #distance between pixels
        
        
    
    

if __name__ == "__main__":
    app = App("Our Awesome GUI!")
    app.mainloop()
