import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from Backend.FileDatabase.database import fileDatabase

class projects_page_base(tk.Frame):
        def __init__(self, parent, fileManager: fileDatabase ):
            super().__init__(parent)
            
            if(type(fileManager) != fileDatabase):
                raise TypeError("fileManager must be of type fileDatabase")
            
            self.fileManager = fileManager
            
            self.new_button = ttk.Button(self, text="New", takefocus=False, command=self.new_popup)
            self.new_button.grid(row=0, column=0, sticky="nswe", padx='10p')

            
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
            self.tree.bind("<Double-1>", self.on_tree_item_double_click)

            self.delete_button = ttk.Button(self, text="Delete Project", command=self.delete_project)
            self.delete_button.grid(row=2, column=1, sticky="nswe", padx='10p', pady='5p')

            self.back_button = ttk.Button(self, text="Back", command=self.go_back)
            self.back_button.grid(pady=5)

            
            self.current_project_id = None
            self.current_folder_id = None
            self.navigation_stack = []  # back navigation stack

            self.load_projects()

        def go_back(self):
            if self.navigation_stack:
                previous_folder_id = self.navigation_stack.pop()
                self.navigate_to_folder(previous_folder_id)
            elif self.current_project_id != None:
                # if you're not currently in a project
                self.current_project_id = None
                self.current_folder_id = None
                self.navigation_stack = []
                self.load_projects()
            else:
                messagebox.showinfo("Navigation", "No previous page to go back to.")

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
                self.tree.insert("", "end", iid=f"project-{project.id}", 
                    values=(project.id, project.name, project.description, getattr(project, "status", "")))
            
        
        def deselect(self):
            self.focus_set()

        
        def get_selected_project_id(self):
            selected_item = self.tree.focus()
            if not selected_item:
                return None

            project_values = self.tree.item(selected_item, 'values')
            if not project_values:
                return None

            return int(project_values[0])  # project ID
        

        def select_project(self):
            project_id = self.get_selected_project_id()
            if project_id is None:
                print("No project selected.")
                return

            try:
                root_folder = self.fileManager.get_project_root(project_id)
                print(f"Selected Project ID: {project_id}, Root Folder ID: {root_folder.id}")
                # Placeholder for future navigation logic
            except Exception as e:
                print(f"Error selecting project: {e}")


        def delete_project(self):
            project_id = self.get_selected_project_id()
            if project_id is None:
                print("No project selected to delete.")
                return

            try:
                self.fileManager.delete_project(project_id)
                self.load_projects()
            except Exception as e:
                print(f"Error deleting project: {e}")


        def create_folder_popup(self):
            if self.current_folder_id is None:
                print("No folder selected to add sub-folder to.")
                return

            win = tk.Toplevel(self)
            win.title("Create Folder")
            win.geometry("300x100")
            win.resizable(False, False)

            ttk.Label(win, text="Folder Name:").grid(row=0, column=0, padx=10, pady=10)
            name_entry = ttk.Entry(win)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            def submit():
                try:
                    name = name_entry.get().strip()
                    self.fileManager.create_folder(name=name, parent_id=self.current_folder_id)
                    self.navigate_to_folder(self.current_folder_id)
                    win.destroy()
                except Exception as e:
                    print(f"Error creating folder: {e}")

            ttk.Button(win, text="Create", command=submit).grid(row=1, column=0, columnspan=2, pady=10)


        def create_file_popup(self):
            if self.current_folder_id is None:
                print("No folder selected to add file to.")
                return

            win = tk.Toplevel(self)
            win.title("Create File")
            win.geometry("300x100")
            win.resizable(False, False)

            ttk.Label(win, text="File Name:").grid(row=0, column=0, padx=10, pady=10)
            name_entry = ttk.Entry(win)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            def submit():
                try:
                    name = name_entry.get().strip()
                    self.fileManager.add_file(name=name, folder_id=self.current_folder_id)
                    self.navigate_to_folder(self.current_folder_id)
                    win.destroy()
                except Exception as e:
                    print(f"Error creating file: {e}")

            ttk.Button(win, text="Create", command=submit).grid(row=1, column=0, columnspan=2, pady=10)

        def new_popup(self):
            win = tk.Toplevel(self)
            win.title("Create New")
            win.geometry("400x200")
            win.resizable(False, False)
            win.grab_set()

            # Dropdown label and menu
            ttk.Label(win, text="What would you like to create?").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            type_box = ttk.Combobox(win, values=["Project", "Folder", "File"], state="readonly")
            type_box.grid(row=0, column=1, padx=10, pady=10, sticky="we")
            type_box.current(0)

            # Name entry
            ttk.Label(win, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
            name_entry = ttk.Entry(win)
            name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

            # Description 
            desc_label = ttk.Label(win, text="Description:")
            desc_entry = ttk.Entry(win)

            def on_type_change(event):
                if type_box.get() == "Project":
                    desc_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                    desc_entry.grid(row=2, column=1, padx=10, pady=5, sticky="we")
                else:
                    desc_label.grid_remove()
                    desc_entry.grid_remove()

            type_box.bind("<<ComboboxSelected>>", on_type_change)
            on_type_change(None)

            # Create button
            create_btn = ttk.Button(win, text="Create")
            create_btn.grid(row=3, column=0, columnspan=2, pady=15)

            def submit():
                name = name_entry.get().strip()
                item_type = type_box.get()
                try:
                    if item_type == "Project":
                        self.fileManager.create_project(name, desc_entry.get().strip())
                        self.load_projects()
                    elif item_type == "Folder":
                        if self.current_folder_id is None:
                            raise ValueError("You must be inside a project or folder to create a new folder.")
                        self.fileManager.create_folder(name, parent_id=self.current_folder_id)
                        self.navigate_to_folder(self.current_folder_id)
                    elif item_type == "File":
                        if self.current_folder_id is None:
                            raise ValueError("You must be inside a folder to create a new file.")
                        self.fileManager.add_file(name, folder_id=self.current_folder_id)
                        self.navigate_to_folder(self.current_folder_id)
                    win.destroy()
                except Exception as e:
                    print(f"Error: {e}")

            create_btn.config(command=submit)

            win.grid_columnconfigure(1, weight=1)  # Allow right-side widgets to expand


        def navigate_to_project(self, project_id):
            self.current_project_id = project_id
            root_folder = self.fileManager.get_project_root(project_id)
            self.tree.delete(*self.tree.get_children())  # clear
            self.tree.insert("", "end", iid=f"folder-{root_folder.id}", values=(root_folder.id, root_folder.name, '', 'Folder'))
            self.navigate_to_folder(root_folder.id)

        def navigate_to_folder(self, folder_id):
            self.current_folder_id = folder_id
            self.tree.delete(*self.tree.get_children())

            folders = self.fileManager.get_child_folders(folder_id, parent_folder=folder_id)
            for folder in folders:
                self.tree.insert("", "end", iid=f"folder-{folder.id}", values=(folder.id, folder.name, '', 'Folder'))

            files = self.fileManager.get_child_files(folder_id)
            for file in files:
                self.tree.insert("", "end", iid=f"file-{file.id}", values=(file.id, file.name, '', 'File'))

        def on_folder_double_click(self, event, item_id):
            selected_item = self.tree.focus()
            if selected_item.startswith("folder-"):
                folder_id = int(selected_item.split("-")[1])
                self.navigation_stack.append(self.current_folder_id)
                self.navigate_to_folder(item_id)

        def on_tree_item_double_click(self, event):
            selected_item = self.tree.focus()
            if not selected_item:
                return
            
            parts = selected_item.split("-")
            if len(parts) != 2:
                print(f"Invalid item ID format: {selected_item}")
                return

            item_type, item_id_str = parts
            item_id = int(item_id_str)

            try:
                if item_type == "project":
                    self.navigate_to_project(item_id)
                elif item_type == "folder":
                    self.on_folder_double_click(event, item_id)
                elif item_type == "file":
                    print("idk yet") 
            except Exception as e:
                print(f"Navigation failed: {e}")
