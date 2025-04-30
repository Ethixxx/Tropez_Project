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


from Backend.API_Connector import requestors
from Backend.API_Key_Container.AccountDB import APIKeyManager
    
    
class MainApp():
    def __init__(self, screenName: str = 'Tropez'):
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
        self.projects_page = self.projects_page_base(self.main_frame)
        self.settings_page = self.settings_page_base(self.main_frame)
        self.accounts_page = self.accounts_page_base(self.main_frame)

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
        
        
    class settings_page_base(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            label = ttk.Label(self, text='Settings Page', font=('Helvetica', 16))
            label.pack(pady=20)
        
        def deselect(self):
            pass
            
    class accounts_page_base(tk.Frame):
        supported_services = {'Google Drive': requestors.GoogleDriveRequestor()}
        def __init__(self, parent):
            super().__init__(parent)

            # New button
            self.new_account_button = ttk.Button(self, text="New", takefocus=False, command=self.add_new_key)
            self.new_account_button.grid(row=0, column=0, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=0, minsize='10p')

            # Search box
            self.search_box = ttk.Entry(self, takefocus=False)
            self.search_box.grid(row=0, column=1, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=1, weight=1, minsize='100p')

            self.PLACEHOLDER = "Search for an account..."
            self.search_box.insert(0, self.PLACEHOLDER)
            self.search_box.configure(foreground='gray')

            self.search_box.bind('<FocusOut>', lambda event: (self.search_box.insert(0, self.PLACEHOLDER), self.search_box.configure(foreground='gray')) if not self.search_box.get() else None)
            self.search_box.bind('<FocusIn>', lambda event: (self.search_box.delete(0, 'end'), self.search_box.configure(foreground='black')) if self.search_box.get() == self.PLACEHOLDER else None)

            # "Sort By" combobox
            self.sort_by_box = ttk.Combobox(self, takefocus=False, state='readonly', width=20)
            self.sort_by_box['values'] = ('Name', 'Service')
            self.sort_by_box.bind("<<ComboboxSelected>>", lambda event: self.load_accounts())
            self.sort_by_box.current(0)
            self.sort_by_box.grid(row=0, column=2, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=2)

            # Treeview to display accounts
            self.tree = ttk.Treeview(self, columns=("ID", "Name", "Service"), show='headings')
            self.tree.heading("ID", text="ID")
            self.tree.heading("Name", text="Name")
            self.tree.heading("Service", text="Service")
            self.tree.grid(row=1, column=0, columnspan=3, sticky="nswe", padx='10p', pady='10p')
            self.grid_rowconfigure(1, weight=1)

            #initialize the database
            db_url = 'sqlite:///api_keys.db'
            self.manager = APIKeyManager(db_url)
            
            # Load data
            self.load_accounts()

        def load_accounts(self):
            # Clear current tree
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get and optionally sort entries
            all_keys = self.manager.list_all_api_keys()

            # Optionally sort
            sort_by = self.sort_by_box.get()
            if sort_by == "Name":
                all_keys.sort(key=lambda x: x[1].lower())
            elif sort_by == "Service":
                all_keys = sorted(all_keys, key=lambda x: self.manager.retrieve_api_key_by_id(x[0])[0].lower())

            # Filter by search term
            query = self.search_box.get()
            if query != self.PLACEHOLDER and query.strip():
                all_keys = [key for key in all_keys if query.lower() in key[1].lower()]

            # Insert into tree
            for key in all_keys:
                service = self.manager.retrieve_api_key_by_id(key[0])[0]
                self.tree.insert("", "end", values=(key[0], key[1], service))
        
        def add_new_key(self):
            #create a pop up box
            self.new_key_window = tk.Toplevel(self)
            self.new_key_window.title("Add New API Key")
            self.new_key_window.geometry("500x200")
            
            #box can not be resized
            self.new_key_window.resizable(width=0, height=0)
            
            #box gets focus
            self.new_key_window.grab_set()
            self.new_key_window.focus_set()
            
            #user added name
            name_label = ttk.Label(self.new_key_window, text="Name:")
            name_label.grid(row=0, column=0, padx='10p', pady='10p')
            
            name_entry = ttk.Entry(self.new_key_window, takefocus=False)
            name_entry.grid(row=0, column=1, padx='10p', pady='10p')
            
            #services dropdown box
            service_label = ttk.Label(self.new_key_window, text="Service:")
            service_label.grid(row=1, column=0, padx='10p', pady='10p')
            
            service_entry = ttk.Combobox(self.new_key_window, takefocus=False, state="readonly")
            service_entry.grid(row=1, column=1, padx='10p', pady='10p')
            service_entry['values'] = list(self.supported_services.keys())
            service_entry.current(0)
            
            #start and cancel button
            start_button = ttk.Button(self.new_key_window, text="Start", takefocus=False, command=lambda: self.start_new_key(name_entry.get(), service_entry.get()))
            start_button.grid(row=2, column=0, padx='10p', pady='10p')
            
            cancel_button = ttk.Button(self.new_key_window, text="Cancel", takefocus=False, command=self.new_key_window.destroy)
            cancel_button.grid(row=2, column=1, padx='10p', pady='10p')
            
            
        def start_new_key(self, name, service):
            #if the name is empty, return
            if not name.strip():
                #highlight the name box in red
                name_entry = self.new_key_window.children['!entry']
                name_entry.configure(foreground='red')
                name_entry.focus_set()
                return
        
            #create a new key for the service and store it in the database
            self.supported_services[service].get_token(name, self.manager)
            '''try:
                self.supported_services[service].get_token(name, self.manager)
            except ValueError as e:
                #if the key already exists, highlight the name box in red
                print(e.with_traceback)
                name_entry = self.new_key_window.children['!entry']
                name_entry.configure(foreground='red')
                name_entry.focus_set()
                return'''
            
            #close the window and reload the accounts page
            self.load_accounts()
            self.new_key_window.destroy()
            
            
        def deselect(self):
            self.focus_set()
            
    class projects_page_base(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            
            #create the new projects button            
            self.new_project_button = ttk.Button(self, text="New", takefocus=False)
            self.new_project_button.grid(row=0, column=0, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=0, minsize='10p')
            
            #create the search box
            self.search_box = ttk.Entry(self, takefocus=False)
            self.search_box.grid(row=0, column=1, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=1, weight=1, minsize='100p')
            
            #configure the placeholder for the search box
            self.PLACEHOLDER = "Search for a project..."
            self.search_box.insert(0, self.PLACEHOLDER)
            self.search_box.configure(foreground='gray')
            
            #configure the placeholder to automatically appear and disapear
            self.search_box.bind('<FocusOut>', lambda event: (self.search_box.insert(0, self.PLACEHOLDER), self.search_box.configure(foreground='gray'))  if not self.search_box.get() else None)
            self.search_box.bind('<FocusIn>', lambda event: (self.search_box.delete(0, 'end'), self.search_box.configure(foreground='black')) if self.search_box.get() == self.PLACEHOLDER else None)
            
            #create the sort by box
            self.sort_by_box = ttk.Combobox(self, takefocus=False, state='readonly', width=20)
            self.sort_by_box['values'] = ('Name', 'Date Created', 'Date Modified')
            self.sort_by_box.bind("<<ComboboxSelected>>", lambda event: event.widget.selection_clear())
            self.sort_by_box.current(0)
            self.sort_by_box.grid(row=0, column=2, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=2)
        
        def deselect(self):
            self.focus_set()
        
    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()