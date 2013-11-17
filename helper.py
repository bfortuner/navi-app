import re
import string
import random
import sys
import ast
from StringIO import StringIO
import pymysql
from models import *
import hashlib
import os
import signal
import math
from config import *


#########  HELPER FUNCTIONS  ##########


# Check if filename includes allowed extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Make secure password with sha256 hash function + salt
def make_salt():
        return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
        if not salt:
                salt = make_salt()
        h = hashlib.sha256(name + pw + salt).hexdigest()
        return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
        salt = h.split('|')[1]
        return h == make_pw_hash(name, pw, salt)



# Handler function if code runs for > 20 seconds
def RuntimeHandler(signum, frame):
    print "Killed. Runtime exceeded maximum runtime"
    sys.exit()



# Determines whether test is unique among other test cases (True or False)
def isUnique(test, test_cases):
        test_defs = []
        for t in test_cases:
                test_defs.append(test_cases[t][0])
        return test_defs.count(test_cases[test][0]) == 1



# Function that returns the category-specific index number of a problem (1,2,3)
def get_category_num(tup1, key):
        count = 0
        for e in tup1:
                if e['problem_id'] == key:
                        return count
                count += 1



# Function that parses test_cases and return test code 
def createTests(testList):
    testString = ''
    i = 1
    testList = ast.literal_eval(str(testList))
    new_list = []
    for test in testList:
	    if test != '':
		    test = str(test.split(" == "))
		    test = ast.literal_eval(test)
		    func = test[0]

		    if type(eval(test[1])) != str:

			    correct_output = '"' + str(test[1]) + '"'
		    else:
			    correct_output = str(test[1])
		    testString += '\nif str(%s) == %s: print """------------------  Test Case %s - Correct!  -------------------"""\nelse: print """------------------  Test Case %s - Incorrect!  ------------------"""\nprint\nprint """  Test Input:  %s"""\nprint\nprint """  Correct Output:  """%s\nprint\nprint """  Your Output:  """ + str(%s)\nprint"""---------------------------------------------------------------"""\nprint\nprint\nprint' % (func, correct_output, str(i), str(i),func, correct_output, func)
		    i += 1
    return testString



# Create tests for newly submitted problem 
def createTestsFromForm(testList):
    testString = ''
    i = 1
    for e in testList:
	    if len(e) > 1:
		    func = e[0]
		    correct_output = e[1]
		    testString += '\nif str(%s) == %s: print """------------------  Test Case %s - Correct!  -------------------"""\nelse: print """------------------  Test Case %s - Incorrect!  ------------------"""\nprint\nprint """  Test Input:  %s"""\nprint\nprint """  Correct Output:  """%s\nprint\nprint """  Your Output:  """ + str(%s)\nprint"""---------------------------------------------------------------"""\nprint\nprint\nprint' % (func, correct_output, str(i), str(i),func, correct_output, func)
    return testString



# Form validation helper functions                                                                                                                                                               
USER_RE = re.compile(r'^[a-zA-Z0-9-_]{3,30}$')
def validUser(username):
        return USER_RE.match(username)

PASS_RE = re.compile(r'^.{3,30}$')
def validPass(password):
        return PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-zA-Z]+')
def validEmail(email):
        return EMAIL_RE.match(email)

TITLE_RE = re.compile(r'[a-zA-Z0-9\'\" _-]+$')
def validTitle(title):
	return TITLE_RE.match(title)

def validDescription(desc):
	desc_list = desc.split()
	return len(desc_list) >= 15

FUNC_NAME = re.compile('([ ]*([a-zA-Z]*|([a-zA-Z][a-zA-Z0-9_]*[a-zA-Z0-9][ ]*)))\(([ ]*([a-zA-Z]*|([a-zA-Z][a-zA-Z0-9_]*[a-zA-Z0-9][ ]*))((,|, )[ ]*([a-zA-Z]|([a-zA-Z][a-zA-Z0-9_]*[a-zA-Z0-9]))[ ]*)*)\)$')
def validFuncName(func_name):
	return FUNC_NAME.match(func_name)

def validCategory(category):
	return category != 'Select Category'

def validSolution(solution, func_name):
	return func_name in solution

def validTests(test_cases, func_name):
	test_status = True
	for test in test_cases:
		if func_name not in test_cases[test][0]:
			test_cases[test][1] = "incorrect"
			test_status = False
	return test_cases, test_status



	


# Function that loads user submitted solutions in to 
def loadUserSub(user_id, problem_id):
        pass


signal.signal(signal.SIGALRM, RuntimeHandler)
# Return output after running python code submitted by user
def getOutputFromFile(str1):
	output = "Your code didn't display any output."
        with open('tests.py', 'w') as myfile:
		myfile.write(str(str1))
        try:
		newbuffer = StringIO()
		sys.stdout = newbuffer
		execfile('tests.py')
		sys.stdout = sys.__stdout__
		if newbuffer.getvalue() == '':
			return "Your code didn't display any output."
		output = newbuffer.getvalue()
	except Exception as e:
		output = e
	finally:
		return output



# Returns problem status based on user history and user 
def checkProblemStatus(user_status=None, testStr=None):
        if testStr != None:
                if "- Correct!  -" in testStr and "- Incorrect!  -" not in testStr:
                        bodySuccess = "Correct!"
                        bodyError = None
                        user_status = "correct"
                        check = u"\u2713"
                else:
                        bodyError = "Incorrect!"
                        bodySuccess = None
                        check = u"\u2718"
                        user_status = "incorrect"
        elif user_status == "incorrect":
                check = u"\u2718"
                bodyError = "Incorrect!"
                bodySuccess = None
        elif user_status == "correct":
                check = u"\u2713"
                bodyError = None
                bodySuccess = "Correct!"
        else:
                check = ''
                bodyError = None
                bodySuccess = None
        return check, bodyError, bodySuccess, user_status



# Checks current cookies for problem_ids and adds user answers to DB during sign 
def addProblemCookies(user, cookies):
	for cookie in cookies:
		regex = re.compile('prob_cookie_[0-9]+')
		if re.match(regex, cookie):
			prob_cookie = eval(cookies[cookie])
			problem_id = re.search("[0-9]+", cookie).group(0)
			user.addUserAnswer(prob_cookie[0], problem_id, prob_cookie[1])
