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
	if username == None:
		flash("Please login to submit a new link", "error")
                return redirect(url_for('login'))
	else:
		user = app.getUser(username)

	if request.method == "POST":
		title = request.form['title']
		url = request.form['url']
		description = request.form['description']
		content_type = request.form['content_type']
		author_id = user.getUserId()
		
		# If not valid inputs...
		if title == '' or url == '':
			if title == '':
				titleError = "Please provide a title for this link"
			else:
				titleError = ""
			if url == '':
				urlError = "Please provide a valid url"
		       	else:
		       		urlError = ""
			return render_template('addlink.html', categories=categories, cat=cat, username=username, url=url, description=description, title=title, urlError=urlError, titleError=titleError)

		else:	
			# Else add link to category
			cat.addLink(title, description, url, category, content_type, author_id)
			return redirect('/c/%s/recent' % category)
	else:
		return render_template('addlink.html', categories=categories, cat=cat, username=username, category=category)



# Create new category for links
@application.route("/addcategory", methods = ["GET","POST"])
@application.route("/c/<category>/addcategory", methods = ["GET","POST"])
def addCategory(category=None, cat_exists_error=None):
	categories = app.getCategories()
	cat = app.getCategory(category)		
       	username = request.cookies.get('username')

	if username == None:
		flash("Please login to create a new category", "error")
                return redirect(url_for('login'))
	else:
		user = app.getUser(username)

	if request.method == "POST":
		title = request.form['title']
		description = request.form['description']
		
		# If not valid inputs
                if title == '' or description == '':
                        if title == '':
                                titleError = "Please provide a title"
                        else:
                                titleError = ""
                        if description == '':
                                descError = "Please provide a short description"
                        else:
                                descError = ""
                        return render_template('addcategory.html', categories=categories, username=username, title=title, description=description, descError=descError, titleError=titleError)

		# Check if category already exists
		new_cat = app.getCategory(title)
		if new_cat == None:			
			# Check for parent category
			if cat != None:
				parent_category = cat.getCategoryName()
				parent_subcategories = cat.getSubcategories()
			else:
				parent_category = None
				parent_subcategories = None
				
			# Else add link to category
			app.addCategory(title, description, parent_category, parent_subcategories)
			return redirect('/c/%s' % title)
		else:
			cat_exists_error = "Sorry that category already exists"
			return render_template('addcategory.html', categories=categories, username=username, description=description, title=title, cat_exists_error=cat_exists_error)
	else:
		return render_template('addcategory.html', categories=categories, username=username)



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
@application.route("/c/<category>/<sort_type>", methods = ["GET","POST"])
@application.route("/c/<category>", methods = ["GET","POST"])
def categoryList(category, sort_type="rating"):
	categories = app.getCategories()
	username = request.cookies.get('username')
	if username != None:
		user = app.getUser(username)
	else:
		user = None

	#Get list of links in category - title, desc, rating
	cat = app.getCategory(category)
	linkList = cat.getLinks(sort_type)

	if request.method == "POST":
		rating = request.form['rate']
		score = rating.split()[0]
		link_id = int(rating.split()[1])

		if user.getUserRating(link_id) == None:
			user.addUserRating(link_id, score)			
		else:
			user.updateUserRating(link_id, score)

		#Refresh list of links in category - title, desc, rating
	       	cat = app.getCategory(category)
	       	linkList = cat.getLinks("rating")

		return render_template("category.html", linkList=linkList, category=category, cat=cat, username=username, categories=categories, user=user, sort_type="rating")
	else:
		return render_template("category.html", linkList=linkList, category=category, cat=cat, username=username, categories=categories, user=user, sort_type=sort_type)


@application.route("/c/<category>/editCat", methods = ["GET","POST"])
def editCategory(category, sort_type="rating", editCat='edit'):
	categories = app.getCategories()
	username = request.cookies.get('username')
	user = app.getUser(username)
	print category
	#Get list of links in category - title, desc, rating
	cat = app.getCategory(category)
	print cat.getCategoryName()
	linkList = cat.getLinks(sort_type)

	if request.method == "POST":
		catSummary = request.form['catSummary']
		cat.editSummary(catSummary)

		return redirect('/c/%s/recent' % category)
	else:
		return render_template("category.html", linkList=linkList, category=category, cat=cat, username=username, categories=categories, user=user, sort_type=sort_type, editCat=editCat)




# Launch application
if __name__ == '__main__':
	application.debug = DEBUG
	application.run(host='0.0.0.0')

		
