import tkinter as tk
from tkinter import ttk
from Backend.FileDatabase.database import fileDatabase
from Backend.API_Key_Container.AccountDB import APIKeyManager
from Backend.API_Connector.FileAdder import FileOrchestrator

class projects_page_base(tk.Frame):
        def __init__(self, parent, fileManager: fileDatabase, apiDatabase: APIKeyManager):
            super().__init__(parent)
            
            self.threaded_file_adder = FileOrchestrator(apiDatabase, fileManager)
            
            if(type(fileManager) != fileDatabase):
                raise TypeError("fileManager must be of type fileDatabase")
            
            if(type(apiDatabase) != APIKeyManager):
                raise TypeError("apiDatabase must be of type APIKeyManager")
            
            self.fileManager = fileManager
            self.APIManager = apiDatabase
            
            #create the new (item) button
            self.new_button = ttk.Button(self, text="New", takefocus=False, command=self.new_popup)
            self.new_button.grid(row=0, column=0, sticky="nwe", padx='10p')

            
            #create the search box
            self.search_box = ttk.Entry(self, takefocus=False)
            self.search_box.grid(row=0, column=1, sticky="nwe", padx='10p', columnspan=2)
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
            self.sort_by_box.grid(row=0, column=3, sticky="nwe", padx='10p')
            self.grid_columnconfigure(index=2)
            
            self.grid_rowconfigure(0, pad='10p', weight=0)
            
            #create the path textbox that spans the columns in row 1
            self.path_textbox = ttk.Label(self, text="Path: ", anchor="w")
            self.path_textbox.grid(row=1, column=0, columnspan=4, sticky="nwe", padx='10p')
            
            #create the project tree
            self.tree = ttk.Treeview(self, columns=("Name", "Description", "Status"), show='headings', selectmode='browse', takefocus=True)
            self.tree.heading("Name", text="Name")
            self.tree.heading("Description", text="Description")
            self.tree.heading("Status", text="Status")
            self.tree.grid(row=2, column=0, columnspan=4, sticky="nswe", padx='10p', pady='10p')
            self.grid_rowconfigure(2, weight=1)
            self.tree.bind("<Double-1>", self.on_tree_item_double_click)
            self.tree.bind("<<TreeviewSelect>>", lambda event: self.on_tree_item_select())

            #create a box to show the full file description of the selected file
            ttk.Label(self, text="Description: ", anchor="w", takefocus=False).grid(row=3, column=0, sticky="we", padx='10p')
            self.description_placeholder = "Select a file to see its description"
            self.file_description = ttk.Label(self, text=self.description_placeholder, anchor="w", justify="left", takefocus=False, foreground="gray")
            self.file_description.config(wraplength=self.file_description.winfo_width())
            self.file_description.bind("<Configure>", lambda event: self.file_description.config(wraplength=self.file_description.winfo_width()))
            self.file_description.grid(row=3, column=1, columnspan=3, sticky="nswe", padx='5p')

            #create the delete button
            self.delete_button = ttk.Button(self, text="Delete", command=self.delete_something, state="disabled")
            self.delete_button.grid(row=4, column=1, sticky="nsww", padx='5p', pady='5p')

            #create the back button
            #create the back button
            self.back_button = ttk.Button(self, text="Back", command=self.go_back, state="disabled")
            self.back_button.grid(pady=5, row=4, column=0)
            
            #create the rename button and input field
            self.rename_button = ttk.Button(self, text="Rename", command=self.rename_something, state="disabled")
            self.rename_button.grid(row=4, column=2, sticky="nsew", padx='10p', pady='5p')
            self.rename_entry = ttk.Entry(self, takefocus=False)
            self.rename_entry.grid(row=4, column=3, columnspan=2, sticky="nswe", padx='10p', pady='5p')
            
            
            #make sure that it is possible to deselect files as expected
            self.tree.bind("<Button-1>", lambda event: self.check_deselect(event))
            
            self.current_project_id = None
            self.current_folder_id = None
            self.navigation_stack = []  # back navigation stack
            self.full_path = ""

            self.update_file_tree()

        def go_back(self):
            if len(self.navigation_stack) > 1:
                self.navigation_stack.pop(-1)
                self.navigate_to_folder(self.navigation_stack[-1])
            else:
                self.full_path = ""
                self.path_textbox.config(text="Path: ")
                self.current_project_id = None
                self.current_folder_id = None
                self.navigation_stack = []
                self.update_file_tree()
                
                self.back_button.config(state="disabled")
            
        
        def create_new_project(self, project_name: str, project_description: str):
            #create a new project in the database
            try:
                self.fileManager.create_project(project_name, project_description)
            except Exception as e:
                #print the error message
                print(e)
                return
            
            #reload the projects to show the new project
            self.update_file_tree()
            

        
        def get_selected_project_id(self):
            selected_item = self.tree.focus()
            if not selected_item:
                return None

            if selected_item.startswith("project-"):
                return int(selected_item.split("-")[1])
    
            return None


        def delete_something(self):
            selected_item = self.tree.focus()
            if not selected_item:
                return None
            
            id = int(selected_item.split("-")[1])
            if selected_item.startswith("project-"):
                try:
                    if(id):
                        self.fileManager.delete_project(id)
                        self.update_file_tree()
                except:
                    print("Project not found")
            elif selected_item.startswith("folder-"):
                try:
                    if(id):
                        self.fileManager.remove_folder(id)
                        self.update_file_tree()
                except:
                    print("Folder not found")
            elif selected_item.startswith("file-"):
                try:
                    if(id):
                        self.fileManager.remove_file(id)
                        self.update_file_tree()
                except:
                    print("File not found")
                    
        def rename_something(self):
            selected_item = self.tree.focus()
            if not selected_item:
                return None
            
            id = int(selected_item.split("-")[1])
            if selected_item.startswith("project-"):
                try:
                    if(id):
                        self.fileManager.rename_project(id, self.rename_entry.get())
                        self.update_file_tree()
                except:
                    print("Project not found")
            elif selected_item.startswith("folder-"):
                try:
                    if(id):
                        self.fileManager.rename_folder(id, self.rename_entry.get())
                        self.update_file_tree()
                except:
                    print("Folder not found")
                    
            self.rename_entry.delete(0, 'end')

        def new_popup(self):
            win = tk.Toplevel(self)
            win.title("Create New")
            win.geometry("600x200")
            win.resizable(False, False)
            win.grab_set()

            # Dropdown label and menu
            ttk.Label(win, text="What would you like to create?").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            type_box = ttk.Combobox(win, values=["Project", "Folder", "File"], state="readonly")
            type_box.grid(row=0, column=1, padx=10, pady=10, sticky="we")
            type_box.current(0)

            # Name entry
            name_label = ttk.Label(win, text="Name:")
            name_entry = ttk.Entry(win)

            # Description 
            desc_label = ttk.Label(win, text="Description:")
            desc_entry = ttk.Entry(win)
            
            # File URL
            url_label = ttk.Label(win, text="URL:")
            url_entry = ttk.Entry(win)

            def on_type_change(event):
                if(type_box.get() == "File"):
                    url_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
                    url_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
                    desc_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                    desc_entry.grid(row=2, column=1, padx=10, pady=5, sticky="we")
                    name_label.grid_remove()
                    name_entry.grid_remove()
                elif(type_box.get() == "Project"):
                    name_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
                    name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
                    desc_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                    desc_entry.grid(row=2, column=1, padx=10, pady=5, sticky="we")
                    url_label.grid_remove()
                    url_entry.grid_remove()
                elif(type_box.get() == "Folder"):
                    name_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
                    name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
                    desc_label.grid_remove()
                    desc_entry.grid_remove()
                    url_label.grid_remove()
                    url_entry.grid_remove()

            type_box.bind("<<ComboboxSelected>>", on_type_change)
            on_type_change(None)
            
            def submit():
                name = name_entry.get().strip()
                item_type = type_box.get()
                try:
                    if item_type == "Project":
                        self.fileManager.create_project(name, desc_entry.get().strip())
                    elif item_type == "Folder":
                        if self.current_folder_id is None:
                            raise ValueError("You must be inside a project or folder to create a new folder.")
                        self.fileManager.create_folder(name, parent_id=self.current_folder_id)
                    elif item_type == "File":
                        if self.current_folder_id is None:
                            raise ValueError("You must be inside a folder to create a new file.")
                        self.threaded_file_adder.queue_add_file(URL=url_entry.get().strip(), folderID=self.current_folder_id, description=desc_entry.get().strip())
                    win.destroy()
                    self.update_file_tree()
                except Exception as e:
                    print(f"Error: {e}")
                    self.update_file_tree()

            # Create button
            create_btn = ttk.Button(win, text="Create", command=submit)
            create_btn.grid(row=3, column=0, pady=15)
            
            #cancel button
            cancel_btn = ttk.Button(win, text="Cancel", command=win.destroy)
            cancel_btn.grid(row=3, column=1, pady=15)


            win.grid_columnconfigure(1, weight=1)  # Allow right-side widgets to expand


        def navigate_to_project(self, project_id):
            self.current_project_id = project_id
            self.navigation_stack = []
            self.full_path = ""
            self.path_textbox.config(text="Path: ")
            root_folder = self.fileManager.get_project_root(project_id)

            self.navigate_to_folder(root_folder.id)
            self.back_button.config(state="normal")

        def navigate_to_folder(self, folder_id):
            self.current_folder_id = folder_id
            if self.current_folder_id in self.navigation_stack:
                index = self.navigation_stack.index(self.current_folder_id)
                # Remove all items after the current index
                self.navigation_stack[:index + 1]
                
                #remake the path textbox
                self.full_path = self.fileManager.get_folder(self.navigation_stack[0]).name
                for folder_id in self.navigation_stack[1:]:
                    folder = self.fileManager.get_folder(folder_id)
                    self.full_path = self.full_path + '/' + folder.name if self.full_path else folder.name
                    
                self.path_textbox.config(text="Path: " + self.full_path)
            else:
                self.navigation_stack.append(self.current_folder_id)
                
                #append the new folder to the path
                new_folder = self.fileManager.get_folder(folder_id)
                self.full_path = self.full_path + '/' + new_folder.name if self.full_path else new_folder.name
                self.path_textbox.config(text="Path: " + self.full_path)
            
            self.update_file_tree()

        def update_file_tree(self):
            # Clear the current file tree
            self.tree.delete(*self.tree.get_children())
            
            if self.current_project_id is not None:
                # Display folders
                folders = self.fileManager.get_child_folders(identifier=self.current_folder_id)
                for folder in folders:
                    self.tree.insert("", "end", iid=f"folder-{folder.id}", values=(folder.name, '', 'Folder'))

                # Display files
                files = self.fileManager.get_child_files(self.current_folder_id)
                for file in files:
                    self.tree.insert("", "end", iid=f"file-{file.id}", values=(file.name, file.description, 'File'))
            else:
                # Clear the navigation stack
                self.navigation_stack = []
                
                # Clear the current project ID
                self.current_project_id = None
                
                # Get the projects from the database
                all_projects = self.fileManager.list_projects()
                
                # Insert the projects into the tree
                for project in all_projects:
                    self.tree.insert("", "end", iid=f"project-{project.id}", 
                        values=(project.name, project.description, project.status))
                
            #sort the tree    
            sort_by = self.sort_by_box.get()
            if sort_by == "Name":
                # Get all items in the tree
                items = [(self.tree.item(item_id, "values")[0], item_id) for item_id in self.tree.get_children()]
                
                # Sort items by the "Name" column (case-insensitive)
                items.sort(key=lambda x: x[0].lower())
                
                # Reinsert items in sorted order
                for index, (name, item_id) in enumerate(items):
                    self.tree.move(item_id, "", index)
                    
            #update the selected item (now None)
            self.deselect()


        def on_tree_item_double_click(self, event):
            selected_item = self.tree.focus()
            if not selected_item:
                return
            
            parts = selected_item.split("-")
            if len(parts) != 2:
                print(f"Invalid item ID format: {selected_item}")
                return

            item_type, item_id = parts
            item_id = int(item_id)

            try:
                if item_type == "project":
                    self.navigate_to_project(item_id)
                elif item_type == "folder":
                    self.navigate_to_folder(item_id)
                elif item_type == "file":
                    import webbrowser
                    file = self.fileManager.get_file(item_id)
                    if file:
                        webbrowser.open(file.URL)
                    else:
                        print(f"File with ID {item_id} not found.")
            except Exception as e:
                print(f"Navigation failed: {e}")
                
        def on_tree_item_select(self):
            selected_item = self.tree.focus()
            if not selected_item:
                selected_item = "reset-0"
                
                
            print("Selected item:", selected_item)
            parts = selected_item.split("-")
            if len(parts) != 2:
                print(f"Invalid item ID format: {selected_item}")
                return

            item_type, item_id = parts
            item_id = int(item_id)

            if item_type == "project":
                self.delete_button.config(state="normal")
                self.delete_button.config(text="Delete Project")
                
                self.file_description.config(text=self.description_placeholder, foreground="gray")
                
                self.rename_button.config(state="normal")
                self.rename_button.config(text="Rename Project")
            elif item_type == "folder":
                self.delete_button.config(state="normal")
                self.delete_button.config(text="Delete Folder")
                
                self.file_description.config(text=self.description_placeholder, foreground="gray")
                
                self.rename_button.config(state="normal")
                self.rename_button.config(text="Rename Folder")
            elif item_type == "file":
                self.delete_button.config(state="normal")
                self.delete_button.config(text="Delete File")
                
                self.file_description.config(text=self.fileManager.get_file(item_id).description, foreground="black")
                
                self.rename_button.config(state="disabled")
                self.rename_button.config(text="Rename")
            else:
                self.delete_button.config(state="disabled")
                self.delete_button.config(text="Delete")
                
                self.file_description.config(text=self.description_placeholder, foreground="gray")
                
                self.rename_button.config(state="disabled")
                self.rename_button.config(text="Rename")
                
        def check_deselect(self, event):
            #check if the coordinates of the click were not on a file in the tree
            x, y = event.x, event.y
            item = self.tree.identify_row(y)
            
            if item:
                # If the click was on a tree item, do nothing
                return
            
            # Otherwise, deselect the tree item
            self.deselect()
            
        
        def deselect(self):
            # Deselect the currently selected item in the treeview
            self.tree.selection_remove(self.tree.selection())
            self.tree.focus('')
            self.on_tree_item_select()
