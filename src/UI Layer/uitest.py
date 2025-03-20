import tkinter as tk
from tkinter import ttk
import ctypes

import threading
import darkdetect #for system dark/light mode detection
import sv_ttk #windows 11 look-alike theme

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

        self.minsize(self.winfo_pixels('300p'), self.winfo_pixels('300p'))

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
        sidebar_width = '40p' #sidebar width is 70 "points" -> 70 * 1/72 inch
        button_height = '40p' #button height is 40 points
        button_padding = '10p' #distance between buttons
        print(sidebar_width)
        
        # Sidebar Frame
        self.sidebar = ttk.Frame(self, width=sidebar_width)
        self.sidebar.pack(side="left", fill="y")
        
        # Shadow Frame (simulates a shadow effect)
        self.shadow = tk.Frame(self, width='1p', background="gray")
        self.shadow.pack(side="left", fill="y")
        
        # Sidebar Buttons (Top Buttons)
        self.btn1 = ttk.Button(self.sidebar, image=tk.PhotoImage(file="C:/Users/Brend/Documents/GitHub/Tropez_Project/src/UI Layer/Icons/folders-svgrepo-com.svg"),
                               takefocus=False,
                               command=lambda: self.show_message("Button 1 clicked"), width=sidebar_width)
        self.btn1.pack(pady=(button_padding, 0), fill="x")
        
        # Separator Below Button 1
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=(5, 5))

        self.btn2 = ttk.Button(self.sidebar, text="Button 2",
                               takefocus=False,
                               command=lambda: self.show_message("Button 2 clicked"), width=sidebar_width)
        self.btn2.pack(pady=(0, 0), fill="x", padx=5)

        # Separator Below Button 2
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=(5, 5))

        # Button Snapped to Bottom with Gear Emoji
        self.btn3 = ttk.Button(self.sidebar, text="⚙️",
                               style="TButton",
                               takefocus=False,
                               command=lambda: self.show_message("Settings clicked"), width=sidebar_width)
        self.btn3.pack(side="bottom", pady=button_padding, fill="x", padx=5)
        
        
        
        
    
    

if __name__ == "__main__":
    app = App("Our Awesome GUI!")
    app.mainloop()
