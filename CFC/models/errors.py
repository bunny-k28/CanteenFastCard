from sqlalchemy import inspect
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime

from datetime import datetime
from . import Base


# Error Message model
class ErrorModel(UserMixin, Base):
    __tablename__ = 'errors'

    eid = Column(Integer, primary_key=True, unique=True)
    emsg = Column(String(200), nullable=False)
    etime = Column(DateTime, nullable=False, default=datetime.utcnow())
    earea = Column(String(100), nullable=False)

    def get_id(self):
        return str(self.eid)

    @classmethod
    def get_column_names(self):
        inspector = inspect(self)
        columns = inspector.columns.keys()
        return list(columns)