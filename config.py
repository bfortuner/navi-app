import os
import base64
import hmac, hashlib

policy_document = '''
{"expiration": "2300-01-01T00:00:00Z",
  "conditions": [ 
    {"bucket": "navi-web"}, 
    ["starts-with", "$key", "uploads/"],
    {"acl": "public-read"},
    {"success_action_redirect": "http://navi-web-env-3mpczhimr3.elasticbeanstalk.com/imageUpload/"},
  ]
}
'''


# configuration                                                                                                                                                                                
DEBUG = True
SECRET_KEY = '298738soinsoba09u2623insk982'


# AWS Access
AWS_ACCESS_KEY_ID = 'AKIAJVYKAG7KLGM5PWHQ'
AWS_SECRET_ACCESS_KEY = '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'
S3_BUCKET_POLICY = base64.b64encode(policy_document)
S3_SIGNATURE = base64.b64encode(hmac.new(AWS_SECRET_ACCESS_KEY, S3_BUCKET_POLICY, hashlib.sha1).digest())


# RDS database                                                                                                                                                                                  
DB_USER = 'bfortuner'
DB_PASSWD = 'AObort90'
DB_HOST = 'redhatdb2.c66nl1qvonl2.us-west-2.rds.amazonaws.com'
DB_NAME = 'navi'


# File upload
module_dir = os.path.dirname(__file__)                                                                                                                                                        
UPLOAD_FOLDER = os.path.join(module_dir, 'static/images/user_profiles/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
