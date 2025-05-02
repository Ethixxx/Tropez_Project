#this file defines the main ui class
import tkinter as tk
from tkinter import ttk
import ctypes

from PIL import Image, ImageTk, ImageOps
import pathlib

# Enable DPI awareness for better scaling on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    print(f"Failed to set DPI awareness: {e}")


from Backend.API_Key_Container.AccountDB import APIKeyManager
from Backend.FileDatabase.database import fileDatabase
from UI_Layer.projectsPage import projects_page_base
from UI_Layer.settingsPage import settings_page_base
from UI_Layer.accountsPage import accounts_page_base
    
    
class MainApp():
    def __init__(self, screenName: str = 'Tropez'):
        self.APIKeyStore = APIKeyManager(db_url="sqlite:///api_keys.db")
        self.fileStore = fileDatabase(db_url="sqlite:///file_database.db")
        
        self.initialize_main_window(screenName)
        self.initialize_main_pages()
        self.initialize_side_bar()
        
    #function initialzies the main window and associated settings
    def initialize_main_window(self, windowTitle: str):
        self.root = tk.Tk()
        self.root.resizable(width=1, height=1)
        self.root.minsize(width=500, height=500)
        self.root.geometry("1000x500")
        self.root.title(windowTitle)
        self.root.grid_rowconfigure(index=0, weight=1)
        
    def initialize_side_bar(self):
        sidebar_width = self.root.winfo_pixels('30p')
        button_height_padding = self.root.winfo_pixels('10p') #distance between buttons
        button_width_padding = self.root.winfo_pixels('5p') #distance between buttons and sides
        button_icon_dimensions = sidebar_width-button_width_padding
        
        # Create the sidebar frame
        self.sidebar = ttk.Frame(self.root, width=sidebar_width)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        
        #within that frame, there is a top and a bottom section
        self.top_sidebar_menu = ttk.Frame(self.sidebar)
        self.top_sidebar_menu.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_rowconfigure(index=0, weight=1) #the top bar will expand

        self.bottom_sidebar_menu = ttk.Frame(self.sidebar)
        self.bottom_sidebar_menu.grid(row=1, column=0, sticky="swe")
        self.sidebar.grid_rowconfigure(index=1, weight=0) #the bottom bar will not expand
        
        #create the top aligned buttons
        icon_directory = pathlib.Path(__file__).parent / "Icons" / "png"
        
        self.projects_icon = ImageTk.PhotoImage(Image.open(icon_directory / r"folders-office-line-2-0.5x.png").resize((button_icon_dimensions, button_icon_dimensions)))
        self.projects_button = tk.Button(self.top_sidebar_menu, image=self.projects_icon, width=sidebar_width, takefocus=False, bd=0, command=lambda: self.change_main_page(self.projects_page))
        self.projects_button.pack(side="top", pady=(button_height_padding, button_width_padding), fill="x")
        
        self.settings_icon = ImageTk.PhotoImage(Image.open(icon_directory / r"settings-office-line-2-0.5x.png").resize((button_icon_dimensions, button_icon_dimensions)))
        self.settings_button = tk.Button(self.top_sidebar_menu, image=self.settings_icon, width=sidebar_width, takefocus=False, bd=0, command=lambda: self.change_main_page(self.settings_page))
        self.settings_button.pack(side="bottom", pady=(button_height_padding, button_width_padding), fill="x")
        
        self.accounts_icon = ImageTk.PhotoImage(Image.open(icon_directory / r"accounts-office-line-2-0.5x.png").resize((button_icon_dimensions, button_icon_dimensions)))
        self.accounts_button = tk.Button(self.top_sidebar_menu, image=self.accounts_icon, width=sidebar_width, takefocus=False, bd=0, command=lambda: self.change_main_page(self.accounts_page))
        self.accounts_button.pack(side="bottom", pady=(button_height_padding, button_width_padding), fill="x")
    
    def initialize_main_pages(self):
        # Separator between sidebar and main content
        self.separator = ttk.Separator(self.root, orient='vertical')
        self.separator.grid(row=0, column=1, sticky='ns')
        self.root.grid_columnconfigure(index=1, weight=0)
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=2, sticky="nswe", pady='10p')
        self.root.grid_columnconfigure(index=2, weight=1)
        self.main_frame.rowconfigure(index=0, weight=1)
        self.main_frame.columnconfigure(index=0, weight=1)
        self.main_frame.grid_propagate(False)
        
        # Create the main pages
        self.projects_page = projects_page_base(self.main_frame, self.fileStore)
        self.settings_page = settings_page_base(self.main_frame)
        self.accounts_page = accounts_page_base(self.main_frame, self.APIKeyStore)

        # place them in the same grid
        self.settings_page.grid(row=0, column=0, sticky="nswe")
        self.settings_page.grid_propagate(False)
        
        self.accounts_page.grid(row=0, column=0, sticky="nswe")
        self.accounts_page.grid_propagate(False)
        
        self.projects_page.grid(row=0, column=0, sticky="nswe")
        self.projects_page.grid_propagate(False)
        
        self.current_page = self.projects_page
        self.change_main_page(self.projects_page)
        
        
    def change_main_page(self, new_page):
        
        #tell the current page it has been deselected
        if(self.current_page != new_page):
            self.current_page.deselect()
        
        #raise the new page to the front
        new_page.tkraise()
        self.current_page = new_page
        
        
    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()