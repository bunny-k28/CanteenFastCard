import os

from flask import redirect, url_for as to
from dotenv import load_dotenv

from CFC.views.admin import admin
from CFC import cfc


load_dotenv(
    os.path.join(
        os.path.abspath(
            os.path.dirname('.')), 
            'site_settings.env')
)

PORT = os.environ.get('PORT')
HOST = os.environ.get('HOST')
DEBUG = os.environ.get('DEBUG')


@cfc.route('/')
def redirectToStudentRoute():
    return redirect(to('student.index'))


# main function for running server
if __name__ == '__main__':
    cfc.run(HOST, PORT, DEBUG)