from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from .. import cfc

from ..models import db
from ..models.admin import AdminModel
from ..models.errors import ErrorModel
from ..models.students import StudentModel
from ..models.feedbacks import FeedbackModel  

class AdminModelView(ModelView):
    column_list = AdminModel.get_column_names()

class StudentModelView(ModelView):
    column_list = StudentModel.get_column_names()

class ErrorModelView(ModelView):
    column_list = ErrorModel.get_column_names()

class FeedbackModelView(ModelView):
    column_list = FeedbackModel.get_column_names()


# This creates a admin panel
admin = Admin(cfc, 'Admin Panel', template_mode='bootstrap4')

admin.add_view(AdminModelView(AdminModel, db, 'Admin'))
admin.add_view(StudentModelView(StudentModel, db, 'Student'))
admin.add_view(ErrorModelView(ErrorModel, db, 'Errors'))
admin.add_view(FeedbackModelView(FeedbackModel, db, 'Feedbacks'))