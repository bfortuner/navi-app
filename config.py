import os

# configuration                                                                                                                                                                                       
DEBUG = True
SECRET_KEY = '298738soinsoba09u2623insk982'


# AWS Access
AWS_ACCESS_KEY_ID = 'AKIAJVYKAG7KLGM5PWHQ'
AWS_SECRET_ACCESS_KEY = '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'

# RDS database                                                                                                                                                                                         
DB_USER = 'bfortuner'
DB_PASSWD = 'AObort90'
DB_HOST = 'redhatdb2.c66nl1qvonl2.us-west-2.rds.amazonaws.com'
DB_NAME = 'navi'


# File upload

module_dir = os.path.dirname(__file__)                                                                                                                                                                                 
UPLOAD_FOLDER = os.path.join(module_dir, 'static/images/user_profiles/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
