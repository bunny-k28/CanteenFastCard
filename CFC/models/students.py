from sqlalchemy import inspect
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String

from . import Base


# Student model
class StudentModel(UserMixin, Base):
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