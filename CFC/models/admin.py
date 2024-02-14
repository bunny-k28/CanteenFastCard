from sqlalchemy import inspect
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String

from . import Base


# Admin model
class AdminModel(UserMixin, Base):
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