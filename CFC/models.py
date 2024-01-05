from sqlalchemy import inspect
from flask_login import UserMixin
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String


# SQLAlchemy setup
DATABASE_URI = 'sqlite:///Database/cfc_userDatabase.db'  # Path to the database file
engine = create_engine(DATABASE_URI, echo=True)  # Set echo=True for debugging SQL statements
Base = declarative_base()

Session = sessionmaker(bind=engine)
db_session = Session()


# Student model
class Student(UserMixin, Base):
    __tablename__ = 'students'
    usid = Column(Integer, primary_key=True, unique=True)
    name = Column(String(50), unique=True, nullable=False)
    pin = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False)
    amount = Column(Integer, nullable=False)

    def get_id(self):
        return str(self.usid)

    @classmethod
    def get_column_names(self):
        inspector = inspect(self)
        columns = inspector.columns.keys()
        return list(columns)


# Admin model
class Admin(UserMixin, Base):
    __tablename__ = 'admins'
    uid = Column(Integer, primary_key=True, unique=True)
    ssid = Column(String(100), unique=True, nullable=True)
    pswd = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)

    def get_id(self):
        return str(self.ssid)

    @classmethod
    def get_column_names(self):
        inspector = inspect(self)
        columns = inspector.columns.keys()
        return list(columns)
