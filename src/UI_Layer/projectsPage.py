import tkinter as tk
from tkinter import ttk
from Backend.FileDatabase.database import fileDatabase

class projects_page_base(tk.Frame):
        def __init__(self, parent, fileManager: fileDatabase ):
            super().__init__(parent)
            
            if(type(fileManager) != fileDatabase):
                raise TypeError("fileManager must be of type fileDatabase")
            
            self.fileManager = fileManager
            
            #create the new projects button            
            self.new_project_button = ttk.Button(self, text="New", takefocus=False, command=self.new_project)
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
            self.sort_by_box['values'] = ('Name', 'Status')
            self.sort_by_box.bind("<<ComboboxSelected>>", lambda event: event.widget.selection_clear())
            self.sort_by_box.current(0)
            self.sort_by_box.grid(row=0, column=2, sticky="nswe", padx='10p')
            self.grid_columnconfigure(index=2)
            
            #create the project tree
            self.tree = ttk.Treeview(self, columns=("Name", "Description", "Status"), show='headings')
            self.tree.heading("Name", text="Name")
            self.tree.heading("Description", text="Description")
            self.tree.heading("Status", text="Status")
            self.tree.grid(row=1, column=0, columnspan=3, sticky="nswe", padx='10p', pady='10p')
            self.grid_rowconfigure(1, weight=1)
            
            self.load_projects()
            
        def new_project(self):
            #create a pop up box
            self.new_project_window = tk.Toplevel(self)
            self.new_project_window.title("Create a new Project")
            self.new_project_window.geometry("500x200")
            
            #box can not be resized
            self.new_project_window.resizable(width=0, height=0)
            
            #box gets focus
            self.new_project_window.grab_set()
            self.new_project_window.focus_set()
            
            #name entry box
            self.project_name_label = ttk.Label(self.new_project_window, text="Project Name:")
            self.project_name_label.grid(row=0, column=0, sticky="nswe", padx='10p')
            self.project_name_entry = ttk.Entry(self.new_project_window, takefocus=True)
            self.project_name_entry.grid(row=0, column=1, sticky="nswe", padx='10p')
            
            #description entry box
            self.project_description_label = ttk.Label(self.new_project_window, text="Project Description:")
            self.project_description_label.grid(row=1, column=0, sticky="nswe", padx='10p')
            self.project_description_entry = ttk.Entry(self.new_project_window, takefocus=True)
            self.project_description_entry.grid(row=1, column=1, sticky="nswe", padx='10p')
            
            #create button
            self.create_button = ttk.Button(self.new_project_window, text="Create", takefocus=False)
            self.create_button.grid(row=2, column=0, sticky="nswe", padx='10p')
            self.create_button.bind("<Button-1>", lambda event: self.create_new_project(self.project_name_entry.get(), self.project_description_entry.get()))
            self.create_button.bind("<Return>", lambda event: self.create_new_project(self.project_name_entry.get(), self.project_description_entry.get()))
            
            #cancel button
            self.cancel_button = ttk.Button(self.new_project_window, text="Cancel", takefocus=False)
            self.cancel_button.grid(row=2, column=1, sticky="nswe", padx='10p')
            self.cancel_button.bind("<Button-1>", lambda event: self.new_project_window.destroy())
            self.cancel_button.bind("<Return>", lambda event: self.new_project_window.destroy())
            
        
        def create_new_project(self, project_name: str, project_description: str):
            #create a new project in the database
            try:
                self.fileManager.create_project(project_name, project_description)
            except Exception as e:
                #blink the name in red
                self.project_name_entry.configure(foreground='red')
                self.project_name_entry.focus_set()
                #print the error message
                print(e)
                return
            
            #reload the projects to show the new project
            self.load_projects()
            
        def load_projects(self):
            #clear the current tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            #get the projects from the database
            all_projects = self.fileManager.list_projects()
            
            #optionally sort the projects
            sort_by = self.sort_by_box.get()
            if sort_by == "Name":
                all_projects.sort(key=lambda x: x.name.lower())
            elif sort_by == "Status":
                all_projects.sort(key=lambda x: x.status.lower())
            
            #insert the projects into the tree
            for project in all_projects:
                self.tree.insert("", "end", values=project)
            
        
        def deselect(self):
            self.focus_set()