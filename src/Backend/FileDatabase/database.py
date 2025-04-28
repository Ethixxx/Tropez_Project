from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    status = Column(String, default='In Progress')
    folders = relationship('Folder', back_populates='project', cascade='all, delete-orphan')

class Folder(Base):
    __tablename__ = 'folders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    project = relationship('Project', back_populates='folders')
    parent = relationship('Folder', remote_side=[id], back_populates='children')
    children = relationship('Folder', back_populates='parent', cascade='all, delete-orphan')
    files = relationship('File', back_populates='folder', cascade='all, delete-orphan')

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=False)
    folder = relationship('Folder', back_populates='files')

# Setup the database
def setup_database(db_url='sqlite:///project_explorer.db'):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Example usage
if __name__ == "__main__":
    Session = setup_database()
    session = Session()
    
    # Create a new project
    new_project = Project(name='My Project')
    session.add(new_project)
    session.commit()
    
    # Add a root folder to the project
    root_folder = Folder(name='Root', project_id=new_project.id)
    session.add(root_folder)
    session.commit()
    
    # Add a nested folder
    subfolder = Folder(name='Subfolder', project_id=new_project.id, parent_id=root_folder.id)
    session.add(subfolder)
    session.commit()
    
    # Add a file inside the subfolder
    file = File(name='document.txt', folder_id=subfolder.id)
    session.add(file)
    session.commit()
    
    print("Project, folders, and file structure created!")
    
    session.close()
