from sqlalchemy import inspect
from flask_login import UserMixin
from sqlalchemy import Column, String

from . import Base


# Error Message model
class FeedbackModel(UserMixin, Base):
    __tablename__ = 'feedbacks'

    fid = Column(String(10), primary_key=True, unique=True)
    feedback = Column(String(250), nullable=False)

    def get_id(self):
        return str(self.fid)

    @classmethod
    def get_column_names(self):
        inspector = inspect(self)
        columns = inspector.columns.keys()
        return list(columns)