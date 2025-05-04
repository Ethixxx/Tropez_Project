from tkinter import Tk, ttk
import tkinter as tk

from Backend.API_Connector import requestors
from Backend.API_Key_Container.AccountDB import APIKeyManager

class accounts_page_base(tk.Frame):
    def __init__(self, parent, APIManager: APIKeyManager = None):
        super().__init__(parent)
        
        if(type(APIManager) != APIKeyManager):
            raise TypeError("APIManager must be of type APIKeyManager")
        self.manager = APIManager

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
        service_entry['values'] = list(requestors.supported_services.keys())
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
        requestors.supported_services[service].get_token(name, self.manager)
        
        #close the window and reload the accounts page
        self.load_accounts()
        self.new_key_window.destroy()
        
        
    def deselect(self):
        self.focus_set()