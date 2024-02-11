import os

from dotenv import load_dotenv
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


# main function for running server
if __name__ == '__main__':
    cfc.run(HOST, PORT, DEBUG)