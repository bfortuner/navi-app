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


# Close current browser window
@application.route('/close_window')
def closeWindow():
	return render_template('close_window.html')
	
	

# Render the Navi homepage!
@application.route("/")
def home(category=None):
	categories = app.getCategories()
	username = request.cookies.get('username')
	return render_template('index.html', categories=categories, username=username, category=category)



# Add user-submitted link to category
@application.route("/c/<category>/addlink", methods = ["GET","POST"])
def addLink(category):
	categories = app.getCategories()
	cat = app.getCategory(category)
       	username = request.cookies.get('username')
	if username != None:
		user = app.getUser(username)
	else:
		user = None

	if request.method == "POST":
		title = request.form['title']
		link = request.form['link']
		description = request.form['description']
		content_type = request.form['content_type']
		author_id = user.getUserId()
		# If not valid inputs...

		# Else add link to category
		cat.addLink(title, description, link, category, content_type, author_id)
		return redirect('/close_window')		
	else:
		return render_template('addlink.html', categories=categories, cat=cat, username=username)



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
@application.route("/c/<category>", methods = ["GET","POST"])
def categoryList(category):
	categories = app.getCategories()
	username = request.cookies.get('username')
	username = None
	if username != None:
		user = app.getUser(username)
	else:
		user = None
	
	#Get list of problems in category - title, desc, difficulty, order
	cat = app.getCategory(category)
	linkList = cat.getLinks()

	if request.method == "POST":
		rating = request.form['rate']
		score = rating.split()[0]
		link_id = int(rating.split()[1])

		if user.getUserDiff(link_id) == None:
			user.addUserDiff(link_id, score)			
		else:
			user.updateUserDiff(link_id, score)
		
		cat = app.getCategory(category)
		linkList = cat.getLinks()

		return render_template("category.html", linkList=linkList, category=category, cat=cat, username=username, categories=categories, user=user)
	else:
		return render_template("category.html", linkList=linkList, cat=cat, username=username, categories=categories, user=user)




# Launch application
if __name__ == '__main__':
	application.debug = DEBUG
	application.run(host='0.0.0.0')

		
