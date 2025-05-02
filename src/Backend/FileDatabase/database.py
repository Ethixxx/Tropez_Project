from typing import NamedTuple
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

FileBase = declarative_base()

class Project(FileBase):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default='In Progress')
    root_folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    folders = relationship('Folder', back_populates='project', cascade='all, delete-orphan', foreign_keys='Folder.project_id')

class Folder(FileBase):
    __tablename__ = 'folders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True, index=True)
    project = relationship('Project', back_populates='folders', foreign_keys=project_id)
    parent = relationship('Folder', remote_side=[id], back_populates='children', foreign_keys=parent_id)
    children = relationship('Folder', back_populates='parent', cascade='all, delete-orphan')
    files = relationship('File', back_populates='folder', cascade='all, delete-orphan', foreign_keys='File.folder_id')

class File(FileBase):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=False, index=True)
    folder = relationship('Folder', back_populates='files', foreign_keys=folder_id)

# Return Types
class ProjectInfo(NamedTuple):
    id: int
    name: str
    description: str
    status: str

class FolderInfo(NamedTuple):
    id: int
    name: str

class FileInfo(NamedTuple):
    id: int
    name: str

class fileDatabase:
    def __init__(self, db_url='sqlite:///project_explorer.db'):
        self.engine = create_engine(db_url)
        FileBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_project(self, name: str, description: str =None):
        session = self.Session()
        
        try:
            # Ensure that the name and description are strings
            if not isinstance(name, str):
                raise ValueError("Project name must be a string.")
            if description is not None and not isinstance(description, str):
                raise ValueError("Project description must be a string.")
            
            # Ensure that a project with that name is not already present
            existing_project = session.query(Project).filter_by(name=name).first()
            if existing_project:
                raise ValueError(f"Project with name '{name}' already exists.")
            
            # Create the project and add it to the database
            new_project = Project(name=name, description=description)
            session.add(new_project)
            session.flush()
            
            # Create the project's dummy folder
            dummy_folder = Folder(name=name + " Root", project=new_project, parent=None)
            session.add(dummy_folder)
            session.flush()
            
            new_project.root_folder_id = dummy_folder.id
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def delete_project(self, identifier: int | str):
        session = self.Session()
        
        try:
            # Find the project and delete it
            if isinstance(identifier, int):
                project = session.query(Project).filter_by(id=identifier).one_or_none()
            elif isinstance(identifier, str):
                project = session.query(Project).filter_by(name=identifier).one_or_none()
            else:
                raise ValueError("Identifier must be an integer or string.")
            
            if not project:
                raise ValueError(f"Project: '{identifier}' does not exist.")
            
            session.delete(project)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def rename_project(self, identifier: int | str, new_name: str):
        session = self.Session()
        
        try:
            # Find the project
            if isinstance(identifier, int):
                project = session.query(Project).filter_by(id=identifier).one_or_none()
            elif isinstance(identifier, str):
                project = session.query(Project).filter_by(name=identifier).one_or_none()
            else:
                raise ValueError("Identifier must be an integer or string.")
            
            if not project:
                raise ValueError(f"Project: '{identifier}' does not exist.")
            
            # Ensure that a project with the new name is not already present
            existing_project = session.query(Project).filter_by(name=new_name).one_or_none()
            if existing_project:
                raise ValueError(f"Project with name '{new_name}' already exists.")
            
            project.name = new_name
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def list_projects(self, max: int = None, skip: int = None) -> list[ProjectInfo]:
        session = self.Session()
        
        try:
            # List all projects with their ids and names
            query = session.query(Project.id, Project.name, Project.description, Project.status)
            
            # Apply pagination rules
            if max is not None:
                query = query.limit(max)
            if skip is not None:
                query = query.offset(skip)
                
            # Execute the query
            query = query.all()
            return [ProjectInfo(*project) for project in query]
            
        except Exception as e:
            raise e
        finally:
            session.close()
    
    def get_project_root(self, project_identifier: int | str):
        session = self.Session()
        
        try:
            #find the project's id if the name was passed
            if(isinstance(project_identifier, str)):
                project = session.query(Project).filter_by(name=project_identifier).one_or_none()
            elif(isinstance(project_identifier, int)):
                project = session.query(Project).filter_by(id=project_identifier).one_or_none()
            else:
                raise ValueError("Identifier must be an integer or string.")
            
            if not project:
                raise ValueError(f"Project: '{project_identifier}' does not exist.")
            
            root_folder = session.query(Folder).filter_by(id=project.root_folder_id).one()
            return FolderInfo(root_folder.id, root_folder.name)
            
        except Exception as e:
            raise e
        finally:
            session.close()

    def create_folder(self, name: str, parent_id: int):
        session = self.Session()
        
        try:
            # Ensure that the parent folder exists
            if parent_id:
                parent_folder = session.query(Folder).filter_by(id=parent_id).one_or_none()
                if not parent_folder:
                    raise ValueError(f"Parent folder: '{parent_id}' does not exist.")
            else:
                raise ValueError("Parent folder ID must be provided.")
            
            # Ensure that a folder with that name is not already present in the parent_folder
            if session.query(Folder).filter_by(name=name, parent_id=parent_id).first():
                raise ValueError(f"Folder with name '{name}' already exists in the project.")
            
            #get the project
            project = parent_folder.project
            
            # Create the folder and add it to the database
            new_folder = Folder(name=name, project=project, parent=parent_folder)
            session.add(new_folder)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    
    def get_child_folders(self, identifier: int | str, parent_folder: int, max: int = None, skip: int = None):
        session = self.Session()
        
        try:
            #find the folder if the name was passed instead of ID
            if(isinstance(identifier, str)):
                if(isinstance(parent_folder, int)):
                    folder = session.query(Folder).filter_by(name=identifier, id=parent_folder).one_or_none()
                else:
                    raise ValueError("Parent folder must be specified when searching for a folder by name.")
            elif(isinstance(identifier, int)):
                folder = session.query(Folder).filter_by(id=identifier).one_or_none()
            else:
                raise ValueError("Identifier must be an integer or string.")
                
            if not folder:
                raise ValueError(f"Folder: '{identifier}' does not exist.")
            
            
            children = session.query(Folder).filter_by(parent_id=folder.id)
            
            if(max is not None):
                children = children.limit(max)
            if(skip is not None):
                children = children.offset(skip)
                
            
            return [FolderInfo(child.id, child.name) for child in children.all()]
            
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_folder_parent(self, folder_id: int):
        session = self.Session()
        
        try:                
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            
            #folder is the root folder
            if(folder.parent_id is None):
                return None
        
            parent_folder = session.query(Folder).filter_by(id=folder.parent_id).one_or_none()
            
            return FolderInfo(parent_folder.id, parent_folder.name)
            
        except Exception as e:
            raise e
        finally:
            session.close()
            
    def add_file(self, name: str, folder_id: int):
        session = self.Session()
        
        try:
            # Ensure that the folder exists
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            
            # Ensure that a file with that name is not already present in the folder
            if session.query(File).filter_by(name=name, folder_id=folder_id).first():
                raise ValueError(f"File with name '{name}' already exists in the folder.")
            
            # Create the file and add it to the database
            new_file = File(name=name, folder=folder)
            session.add(new_file)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def get_child_files(self, folder_id: int, max: int = None, skip: int = None):
        session = self.Session()
        
        try:
            #find the folder
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            
            files = session.query(File).filter_by(folder_id=folder.id)
            
            if(max is not None):
                files = files.limit(max)
            if(skip is not None):
                files = files.offset(skip)
                
            return [FileInfo(file.id, file.name) for file in files.all()]
            
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_file_parent(self, file_id: int):
        session = self.Session()
        
        try:
            file = session.query(File).filter_by(id=file_id).one_or_none()
            
            if not file:
                raise ValueError(f"File: '{file_id}' does not exist.")
            
            folder = session.query(Folder).filter_by(id=file.folder_id).one_or_none()
            
            return FolderInfo(folder.id, folder.name)
            
        except Exception as e:
            raise e
        finally:
            session.close()
            
    def get_file_project(self, file_id: int):
        session = self.Session()
        
        try:
            file = session.query(File).filter_by(id=file_id).one_or_none()
            
            if not file:
                raise ValueError(f"File: '{file_id}' does not exist.")
            
            folder = session.query(Folder).filter_by(id=file.folder_id).one_or_none()
            project = session.query(Project).filter_by(id=folder.project_id).one_or_none()
            
            return ProjectInfo(project.id, project.name, project.description, project.status)
            
        except Exception as e:
            raise e
        finally:
            session.close()
        
    def get_folder_project(self, folder_id: int):
        session = self.Session()
        
        try:
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            
            project = session.query(Project).filter_by(id=folder.project_id).one_or_none()
            
            return ProjectInfo(project.id, project.name, project.description, project.status)
            
        except Exception as e:
            raise e
        finally:
            session.close()
            
    def remove_folder(self, folder_id: int):
        session = self.Session()
        
        try:
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            
            # Don't delete the root folder
            if folder.parent_id is not None:
                # Delete the folder and all its children
                session.delete(folder)
                session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def remove_file(self, file_id: int):
        session = self.Session()
        
        try:
            file = session.query(File).filter_by(id=file_id).one_or_none()
            
            if not file:
                raise ValueError(f"File: '{file_id}' does not exist.")
            
            # Delete the file
            session.delete(file)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def move_file(self, file_id: int, new_folder_id: int):
        session = self.Session()
        
        try:
            file = session.query(File).filter_by(id=file_id).one_or_none()
            
            if not file:
                raise ValueError(f"File: '{file_id}' does not exist.")
            
            #if file is already in the new folder
            if(file.folder_id == new_folder_id):
                return
            
            #find the new folder
            new_folder = session.query(Folder).filter_by(id=new_folder_id).one_or_none()
            
            if not new_folder:
                raise ValueError(f"New Folder: '{new_folder_id}' does not exist.")
            
            # Move the file to the new folder
            file.folder = new_folder
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def move_folder(self, folder_id: int, new_parent_id: int):
        session = self.Session()
        
        try:
            folder = session.query(Folder).filter_by(id=folder_id).one_or_none()
            
            if not folder:
                raise ValueError(f"Folder: '{folder_id}' does not exist.")
            elif (folder.parent is None):
                raise ValueError("Cannot move the root folder.")
            elif (folder.parent_id == new_parent_id):
                #if folder is already in the new parent folder
                return
            
            #find the new parent folder
            new_parent = session.query(Folder).filter_by(id=new_parent_id).one_or_none()
            
            if not new_parent:
                raise ValueError(f"New Parent Folder: '{new_parent_id}' does not exist.")
            
            # Move the folder to the new parent
            folder.parent = new_parent
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# Example usage
if __name__ == "__main__":
    db = fileDatabase()
    
    # Create a project
    print("Creating a project...")
    db.create_project(name="Project A", description="This is Project A")
    db.create_project(name="Project B", description="This is Project B")

    # List all projects
    print("\nListing all projects:")
    projects = db.list_projects()
    for project in projects:
        print(f"ID: {project.id}, Name: {project.name}, Description: {project.description}, Status: {project.status}")

    # Get the root folder of the project
    print("\nGetting the root folder of 'Project A':")
    root_folder = db.get_project_root("Project A")
    print(f"Root Folder ID: {root_folder.id}, Name: {root_folder.name}")

    # Add child folders to the root folder
    print("\nAdding child folders to the root folder...")
    db.create_folder(name="Child Folder 1", parent_id=root_folder.id)
    db.create_folder(name="Child Folder 2", parent_id=root_folder.id)

    # List child folders of the root folder
    print("\nListing child folders of the root folder:")
    child_folders = db.get_child_folders(identifier=root_folder.id, parent_folder=root_folder.id)
    for folder in child_folders:
        print(f"ID: {folder.id}, Name: {folder.name}")

    # Add files to a child folder
    print("\nAdding files to 'Child Folder 1'...")
    child_folder_1_id = child_folders[0].id
    db.add_file(name="File 1", folder_id=child_folder_1_id)
    db.add_file(name="File 2", folder_id=child_folder_1_id)

    # List files in 'Child Folder 1'
    print("\nListing files in 'Child Folder 1':")
    files = db.get_child_files(folder_id=child_folder_1_id)
    for file in files:
        print(f"ID: {file.id}, Name: {file.name}")

    # Move a file to 'Child Folder 2'
    print("\nMoving 'File 1' to 'Child Folder 2'...")
    file_1_id = files[0].id
    child_folder_2_id = child_folders[1].id
    db.move_file(file_id=file_1_id, new_folder_id=child_folder_2_id)

    # Verify the file's new location
    print("\nVerifying the file's new location:")
    file_parent = db.get_file_parent(file_id=file_1_id)
    print(f"File ID: {file_1_id} is now under Folder ID: {file_parent.id}, Name: {file_parent.name}")

    # Move 'Child Folder 1' under 'Child Folder 2'
    print("\nMoving 'Child Folder 1' under 'Child Folder 2'...")
    db.move_folder(folder_id=child_folder_1_id, new_parent_id=child_folder_2_id)

    # Verify the new parent of 'Child Folder 1'
    print("\nVerifying the new parent of 'Child Folder 1':")
    folder_parent = db.get_folder_parent(folder_id=child_folder_1_id)
    print(f"Child Folder 1 is now under Folder ID: {folder_parent.id}, Name: {folder_parent.name}")

    # Delete a file
    print("\nDeleting 'File 2'...")
    db.remove_file(file_id=files[1].id)

    # Delete a folder
    print("\nDeleting 'Child Folder 1'...")
    db.remove_folder(folder_id=child_folder_1_id)

    # Clean Up
    print("\nDeleting 'Project A'...")
    db.delete_project(identifier="Project A")
    
    print("\nDeleting 'Project B'...")
    db.delete_project(identifier="Project B")

    print("\nAll operations completed successfully!")