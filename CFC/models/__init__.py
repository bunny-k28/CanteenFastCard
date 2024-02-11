import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base


# SQLAlchemy setup
DATABASE_URI = 'sqlite:///' + os.path.join(
    os.path.abspath(os.path.dirname('.')), 
    'Database', 'cfc_userDatabase.db') # Path to the database file

engine = create_engine(DATABASE_URI)  # Set echo=True for debugging SQL statements
Base = declarative_base()

Session = sessionmaker(bind=engine)
db = Session()