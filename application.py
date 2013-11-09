#!/usr/bin/env python
from flask import *
import re
import sys
from StringIO import StringIO
import pymysql
import ast
import random
from helper import *
from models import *
from config import *
import signal
import os




#############  VIEW FUNCTIONS  ##############


# Create new account for user
@application.route('/signup', methods= ['GET', 'POST'])
def signup():
	username = request.cookies.get('username')
	categories = app.getCategories()

	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
		verify = request.form['verify']
		email = request.form['email']


		if validUser(username) and validPass(password) and validEmail(email) and password == verify:
			user = app.getUser(username)
			if user == None:
				password = make_pw_hash(username, password)
				# Create user instance and add to users table in db
				user = app.addUser(username, password, email)
				
				# Add problem cookies into db
				addProblemCookies(user, request.cookies)

				# Return user to homepage after sign up
				resp = make_response(redirect(url_for('home')))
				resp.set_cookie('username',username)
				return resp

			else:
				userExists = "Sorry that username already exists!"
				return render_template('signup.html', userExists=userExists, username=username, categories=categories, category=None)

		else:
			if not validUser(username):
				userError = "Sorry that is not a valid username"
			else:
				userError = ""
			if not validPass(password):
				passError = "Sorry that is not a valid password"
			else:
				passError = ""
			if password != verify:
				verifyError = "Sorry those passwords don't match"
			else:
				verifyError = ""
			if not validEmail(email):
				emailError = "Sorry that is not a valid email"
			else:
				emailError = ""
			return render_template('signup.html', username=username, email=email, userError=userError, passError=passError, verifyError=verifyError, \
					       emailError=emailError, user_cookie=username, categories=categories, category=None)
	else:
		return render_template('signup.html', user_cookie=username, categories=categories, category=None)



# User login
@application.route('/login', methods=['POST', 'GET'])
def login():
	categories = app.getCategories()
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
		user = app.getUser(username)

		if user:
			if valid_pw(username, password, user.getPassword()):
				resp = make_response(redirect(url_for('home')))
				resp.set_cookie('username', username)
				return resp
			else:
				passError = "Sorry that password is not correct"
				return render_template('login.html', passError=passError, username='', categories=categories, category=None)			
		else:
			if not user:
				userError = "Sorry that username does not exist"
				return render_template('login.html', userError=userError, username='', categories=categories, category=None)
			elif password != user.getPassword():
				passError = "Sorry that password is not correct"
				return render_template('login.html', passError=passError, username='', categories=categories, category=None)
	else:
		return render_template('login.html', categories=categories, category=None)



# Logout user and clear all cookies
@application.route('/logout')
def logout():
	resp = make_response(redirect(url_for('home')))
	for cookie in request.cookies:
		resp.set_cookie(cookie, "", expires=0)
	return resp



# Render the Problee homepage!
@application.route("/")
def home(category=None):
	categories = app.getCategories()
	username = request.cookies.get('username')
	problem_count = app.getProbCount()
	return render_template('index.html', categories=categories, username=username, category=category, problem_count=problem_count)



# Function that picks a random problem in problem library - need to fix this to incorporate a "shuffle" playlist
@application.route('/problem/<category>/<int:problem_id>/random', methods = ["GET"])
def randomProblem(problem_id, category):
	new_prob_id = app.getRandomProblem(problem_id, category)
	return redirect('/problem/%s/%s' % (category, new_prob_id))		



# Function that powers "Next" and "Back" problem navigation within categories
@application.route("/mv/<direction>/<category>/<int:problem_id>", methods = ["GET"])
def changeProblem(direction,category,problem_id):
	next_problem_id = app.getNextProblem(problem_id, category, direction)
	return redirect('/problem/%s/%s' % (category, next_problem_id))




# Category page that returns list of problems in category
@application.route("/problem/<category>", methods = ["GET","POST"])
def categoryList(category):
	categories = app.getCategories()
	username = request.cookies.get('username')
	if username != None:
		user = app.getUser(username)
	else:
		user = None
	
	#Get list of problems in category - title, desc, difficulty, order
	cat = app.getCategory(category)
	probList = cat.getProbs()

	if request.method == "POST":
		rating = request.form['rate']
		score = rating.split()[0]
		problem_id = int(rating.split()[1])

		if user.getUserDiff(problem_id) == None:
			user.addUserDiff(problem_id, score)			
		else:
			user.updateUserDiff(problem_id, score)
		
		cat = app.getCategory(category)
		probList = cat.getProbs()

		return render_template("category.html", probList=probList, category=category, cat=cat, username=username, categories=categories, user=user)
	else:
		return render_template("category.html", probList=probList, category=category, cat=cat, username=username, categories=categories, user=user)




# Primary problem page that displays problems and provides feedback
@application.route("/problem/<int:problem_id>", methods = ["GET","POST"])
@application.route("/problem/<category>/<int:problem_id>", methods = ["GET","POST"])
def problem(problem_id, category=None, solution=None, user_status=None, userAnswer=None, prob_cookie=None):

	categories = app.getCategories()

	# pull any existing cookies for username and past user solution to problem
	username = request.cookies.get('username')
	if request.cookies.get('prob_cookie_' + str(problem_id)) != None:
		prob_cookie = eval(request.cookies.get('prob_cookie_' + str(problem_id)))


	# pull problem details from problems table
	prob = app.getProblem(problem_id)


	# if problem_id doesn't exist, redirect user to first problem
	if prob == None:
		return redirect('/problem/1')
		

		
	# Pull user_id and userAnswer from users table if user is logged in
	if username != None:
		user = app.getUser(username)
		user_id = user.getUserId()
		userAnswer = user.getUserAnswer(problem_id)
		if userAnswer != None:
			if userAnswer[0] != None:
				body = userAnswer[0]
				user_status = userAnswer[1]
			else:
				body = prob.getFuncName()
		elif prob_cookie != None:
			body = prob_cookie[0]
			user_status = prob_cookie[1]
		else:
			body = prob.getFuncName()
			
	# Pull any existing cookies if user has worked on problem previously
	elif prob_cookie != None:
	       	body = prob_cookie[0]
	       	user_status = prob_cookie[1]
	
	# Return default func_name as value inside coding editor 
	else:
		body = prob.getFuncName()


	# Set problem status using user_status (correct? incorrect? green check? red 'X'?)
	check, bodyError, bodySuccess, user_status = checkProblemStatus(user_status=user_status)

	
	# If user submits code for grading
	if request.method == "POST":
		body = request.form["codingArea"]
		tests = createTests(prob.getTests())
		
		# If user clicks 'Show Solution', reload page with solution visible
		if request.form["button"] == 'Show Solution':
			return render_template("problem.html", problem_id=problem_id, solution=prob.getSolution(), body=body, test='', title=prob.getTitle(), \
					       desc=prob.getDesc(), bodySuccess=bodySuccess, bodyError=bodyError, check=check, output='', category=prob.getCategory(), \
					       username=username, user_status=user_status, categories=categories, category_position=prob.getCategoryPosition())

		# Run user code and get output without tests
		try:
			# Set the signal handler and a 5-second alarm
			output = getOutputFromFile(body)
			
		except Exception as e:
			output = e


		try: 
			test = getOutputFromFile(body + tests)
			#test = test.replace(output,'', 1)
			
		except Exception as e:
			test = e
		
		# Return page with output + tests filled out for the user
                finally:
			check, bodyError, bodySuccess, user_status = checkProblemStatus(testStr=test)

			# If user is logged in, and has worked on the problem previously, update his answer in DB
			if userAnswer != None and username != None:
				user.updateUserAnswer(problem_id, body, user_status)

			# If user is logged in, but has not worked on problem previously, add new answer to DB
			elif body != prob.getFuncName() and username != None: 
				user.addUserAnswer(body, problem_id, user_status)

			resp = make_response(render_template("problem.html", problem_id=problem_id, solution=solution, body=body, test=test, title=prob.getTitle(), \
							     desc=prob.getDesc(), bodySuccess=bodySuccess, bodyError=bodyError, check=check, output=output, category=prob.getCategory(), \
							     username=username, user_status=user_status, categories=categories, category_position=prob.getCategoryPosition()))
			resp.set_cookie('prob_cookie_' + str(problem_id), str([body, user_status]))
			return resp

	# Return page for GET request
	else:
		return render_template("problem.html", problem_id=problem_id, body=body,title=prob.getTitle(), solution=solution, desc=prob.getDesc(), bodyError=bodyError, \
				       bodySuccess=bodySuccess, check=check, category=prob.getCategory(), username=username, user_status=user_status, categories=categories, \
				       category_position=prob.getCategoryPosition())





# Lets users add new problems
@application.route("/add_problem", methods = ["GET","POST"])
def add_problem(titleError='', funcNameError='', categoryError='', descError='', solutionError='', testError='', category="Select Category", checks={'2':'','1':''}):
	categories = app.getCategories()
	catDropdown = CATEGORIES
	username = request.cookies.get('username')
	test_cases = {'test1': ['', 'None'], 'test2': ['', 'None'], 'test3': ['', 'None'], 'test4': ['', 'None'], 'test5': ['', 'None']}
		
	# Require that user log in before submitting a problem
	if username == None:
		flash("Please login to submit a new problem", "error")
		return redirect(url_for('home'))
	else:
		user = app.getUser(username)
		user_id = user.getUserId()


	
	# If user submits code for grading
	if request.method == "POST":
		checks = {'correct':u"\u2713",'incorrect':u"\u2718"}
		
		# Pull user submitted values from form
		solution = request.form["codingArea"]
		title = request.form["title"]
		desc = request.form["desc"]
		func_name = request.form["func_name"].replace('def ','').replace(':','')
		category = request.form["category"]
		test1 = request.form["test1"].strip().encode('ascii','ignore')
		test2 = request.form["test2"].strip().encode('ascii','ignore')
		test3 = request.form["test3"].strip().encode('ascii','ignore')
		test4 = request.form["test4"].strip().encode('ascii','ignore')
		test5 = request.form["test5"].strip().encode('ascii','ignore')
		
		# Add user submitted test cases to dictionary
		test_cases = {'test1': [test1, 'None'], 'test2': [test2, 'None'], 'test3': [test3, 'None'], 'test4': [test4, 'None'], 'test5': [test5, 'None']}
		

		# Run user submitted code to generate output WITHOUT test cases 
		try:	
			output = getOutputFromFile(solution)
		except Exception as e:
			output = e
			solutionError = 'Invalid solution'
			
		status = True
		
		# Check if solution passes all test cases
		test_count = 0
		for test in test_cases:

			# Check if test cases is duplicate or left blank
			if test_cases[test][0] != '' and isUnique(test, test_cases):
				
				# Run code with test case and check if test case evaluates to True
				try:
					out = getOutputFromFile(solution + "\nprint " + test_cases[test][0]).strip()
					if out[-4:] == "True":
						test_cases[test][1] = "correct"
					else:
						testError = 'Please input at least 3 unique test cases'
						status = False
						test_cases[test][1] = "incorrect"
					test_count += 1
				except Exception:
					testError = 'Please input at least 3 unique test cases'
					status = False
					test_cases[test][1] = "incorrect"
					
			elif test_cases[test][0] != '':
				# If test case is duplicate
				testError = 'Please input at least 3 unique test cases'
				status = False
				test_cases[test][1] = "incorrect"
			
			else:
				pass


		print test_cases
		if test_count < 3:
			testError = 'Please input at least 3 unique test cases'
			status = False

			
		# If user submits form, check if form is filled out correctly
		if request.form['button'] == "Submit":
			
			# Pull list of titles from DB to check if title already exists
			title_list = app.getProblemTitles()
			if not validTitle(title):
				status = False
				titleError = 'Please input a valid title'
			for t in title_list:
				if t['title'] == title:
					status = False
					titleError = 'Sorry that title already exists. Please choose a different title.'
			if not validFuncName(func_name):
				status = False
				funcNameError = 'Please input a valid function definition.'
			if not validDescription(desc):
				status = False
				descError = 'Problem explanation must be at least 20 words.'
			if not validSolution(solution, func_name):
				status = False
				solutionError = 'Please include the function definition in the solution.'
			if not validCategory(category):
				status = False
				categoryError = 'Please select a category.'
		

			# If user submitted problem is valid, add problem to database
			if status == True:
				tests = []
				for test in test_cases:
					tests.append(test_cases[test][0])
				tests = str(tests)
				new_prob = app.addProblem(title, category, desc, func_name, solution, tests, user_id)

				# Redirect to newly created problem page
				flash("Congratulations! New problem successfully created!", "success")
				return redirect('/problem/%s' % new_prob.getProblemId())
			

		# If user clicks "Test Run", display the code output but do not evaluate the form submissions
		return render_template("add_problem.html", title=title, desc=desc, func_name=func_name, solution=solution, category=category, username=username, \
				       categories=categories, test1=test1, test2=test2, test3=test3, test4=test4, test5=test5, output=output, test_cases=test_cases, \
				       checks=checks, titleError=titleError, funcNameError=funcNameError, descError=descError, solutionError=solutionError, \
				       categoryError=categoryError, testError=testError, catDropdown=catDropdown)
	else:
		# Return default page if GET request
		return render_template("add_problem.html", solution='', title='', desc='', func_name='', category=category, username=username, categories=categories, \
				      test_cases=test_cases, checks=checks, catDropdown=catDropdown)





# Launch application
if __name__ == '__main__':
	application.debug = DEBUG
	application.run(host='0.0.0.0')

		
