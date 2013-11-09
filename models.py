from flask import *
import pymysql
import ast
import re
from config import *



# Category class which holds list of problem objects
class Category(object):
	def __init__(self, name):
		self.name = name
		self.problems = self.genProbList()

	def getProbCount(self):
		return len(self.problems)

	def genProbList(self, order="ASC"):
		probs = []
		g.db.execute('SELECT problem_id, title, description, solution, tests, func_name, ROUND(difficulty_sum/difficulty_votes,2) as difficulty, difficulty_votes FROM problems WHERE category = %s ORDER BY difficulty ASC;', [self.name])
		problems = g.db.fetchall()
		for p in problems:
		     problem_id = p['problem_id']
		     title = p['title']
		     desc = p['description']
		     solution = p['solution']
		     tests = p['tests']
		     func_name = p['func_name']
		     category_position = 1
		     difficulty = p['difficulty']
		     difficulty_votes = p['difficulty_votes']
		     newProb = Problem(problem_id, title, desc, solution, tests, self.name, func_name, category_position, difficulty, difficulty_votes)
		     probs.append(newProb)
		return probs
		
	def getProbs(self):
		return self.problems

	def getCategoryName(self):
		return self.name



# Application class which includes high level functions to manipulate User and Problem instances
class App(object):
	def __init__(self):
		self.application = Flask(__name__)
		self.secret_key = 'secret2222'

	# Return number of unique problems in database
	def getProbCount(self, category=None):
		if category != None:
			g.db.execute('select count(problem_id) as problem_count FROM problems WHERE category = %s', [category])
		else:
			g.db.execute('select count(problem_id) as problem_count FROM problems')
		problem = g.db.fetchone()
		return problem['problem_count']


	# Returns list of problem titles in database
	def getProblemTitles(self):
		g.db.execute("SELECT title FROM problems")
		title_list = g.db.fetchall()
		return title_list
	


	# Returns list of categories in problem lib 
	def getCategories(self):
		g.db.execute('SELECT category, count(problem_id) as problem_count, MIN(problem_id) as min_problem_id FROM problems GROUP BY category ORDER BY count(problem_id) DESC;')
		categories = g.db.fetchall()
		return categories


	# Returns a list with [problem position in category, length of category] 
	def getCategoryPosition(self, problem_id, category):
		g.db.execute('SELECT COUNT(CASE WHEN problem_id < %s THEN problem_id ELSE NULL END) + 1 as current_prob, count(problem_id) as total_probs FROM problems WHERE category = %s ORDER BY problem_id ASC;', [problem_id, category])
		problem = g.db.fetchone()
		return problem
	
	# Add new user to the database
	def addUser(self, username, password, email):
		g.db.execute("INSERT INTO users (username, password, email) VALUES (%s,%s,%s)", [username, password, email])
		g.conn.commit()

		g.db.execute('SELECT user_id FROM users WHERE username = %s;', [username])
		user = g.db.fetchone()
		user_id = user['user_id']
		return User(user_id, username, password, email)

	# If user in database return User object, else return None
	def getUser(self, username):
		g.db.execute('SELECT user_id, password, email FROM users WHERE username = %s;', [username])
		user = g.db.fetchone()

		if user != None:
			password = user['password']
			email = user['email']
			user_id = user['user_id']
			return User(user_id, username, password, email)
		else:
			return None


	# Add a new user submitted problem to the db
	def addProblem(self, title, category, desc, func_name, solution, tests, author_id):
		g.db.execute("INSERT INTO problems (title, category, description, func_name, solution, tests, author_id) VALUES (%s, %s, %s, %s, %s, %s, %s);", [title, category, desc, func_name, solution, tests, author_id])
		g.conn.commit()

		g.db.execute('SELECT problem_id FROM problems WHERE title = %s;', [title])
		prob = g.db.fetchone()
		problem_id = prob['problem_id']
		return Problem(problem_id, title, desc, solution, tests, category, func_name, app.getCategoryPosition(problem_id, category))

	
	# Return a problem object to the user
	def getProblem(self, problem_id):
		g.db.execute('SELECT *, ROUND(difficulty_sum/difficulty_votes,2) as difficulty FROM problems WHERE problem_id = %s;', [problem_id])
		problem = g.db.fetchone()
		if problem == None:
			return None
		else:
			title = problem['title']
			desc = problem['description']
			tests = ast.literal_eval(problem['tests'])
			category = problem['category']
			func_name = problem['func_name']
			category_position = app.getCategoryPosition(problem_id, category)
			solution = problem['solution']
			difficulty = problem['difficulty']
			difficulty_votes = problem['difficulty_votes']
			return Problem(problem_id, title, desc, solution, tests, category, func_name, category_position, difficulty, difficulty_votes)



	# Return a category object with list of problems
	def getCategory(self, name):
		return Category(name)
	



	# Return the next or previous problem in the same category
	def getNextProblem(self, problem_id, category, direction):
		if direction == 'next':
			g.db.execute('select min(problem_id) as new_prob_id from problems where problem_id > %s and category = %s ;', [problem_id, category])
			nextProb = g.db.fetchone()
			if nextProb['new_prob_id'] != None:
				next_problem_id = nextProb['new_prob_id']
			else:
				g.db.execute('select min(problem_id) as new_prob_id from problems where category = %s;', [category])
				nextProb = g.db.fetchone()
				next_problem_id = nextProb['new_prob_id']
		else:
			g.db.execute('select max(problem_id) as new_prob_id from problems where problem_id < %s and category = %s ;', [problem_id, category])
			nextProb = g.db.fetchone()
			if nextProb['new_prob_id'] != None:
				next_problem_id = nextProb['new_prob_id']
			else:
				g.db.execute('select min(problem_id) as new_prob_id from problems where category = %s;', [category])
				nextProb = g.db.fetchone()
				next_problem_id = nextProb['new_prob_id']
		return next_problem_id


	# Return a random problem in the same category
	def getRandomProblem(self, problem_id, category):
		g.db.execute('select problem_id, rand() FROM problems WHERE problem_id != %s and category = %s GROUP BY problem_id, rand() ORDER BY rand() LIMIT 1;', [problem_id, category])
		problem = g.db.fetchone()
		if problem != None:
			return problem['problem_id']
		return problem_id




# Initialize the application to support view functions
app = App()
application = app.application
application.secret_key = app.secret_key




# Initialize RDS database connection before request                                                                                                                                                    
@application.before_request                                                                                                                                                                       
def before_request():                                                                                                                                                                              
	g.conn = pymysql.connect(db=DB_NAME, user=DB_USER, passwd=DB_PASSWD, host=DB_HOST)
	g.db = g.conn.cursor(pymysql.cursors.DictCursor)
	#g.conn = pymysql.connect(db='test', unix_socket='/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock', user='root', passwd='')                                                          



# End RDS database connection after request                                                                                                                                                  
@application.teardown_request                                                                                                                                                                     
def teardown_request(exception=None):                                                                                                                                                                 
	g.conn.close()   





# Problem class
class Problem(object):
	def __init__(self, problem_id, title, desc, solution, tests, category, func_name, category_position, difficulty, difficulty_votes):
		self.problem_id = problem_id
		self.title = title
		self.desc = desc
		self.solution = solution
		self.tests = tests
		self.category = category
		self.func_name = func_name
		self.category_position = category_position
		self.difficulty = difficulty
		self.difficulty_votes = difficulty_votes

	def getTitle(self):
		return self.title

	def getProblemId(self):
		return self.problem_id

	def getDesc(self):
		return self.desc

	def getSolution(self):
		return self.solution

	def getTests(self):
		return self.tests

	def getCategory(self):
		return self.category

	def getFuncName(self):
		return 'def ' + str(self.func_name) + ':'

	def getCategoryPosition(self):
		return self.category_position

	def getDifficulty(self):
		return self.difficulty

	def getDifficultyVotes(self):
		return self.difficulty_votes



# User class
class User(object):
	def __init__(self, user_id, username, password, email):
		self.user_id = user_id
		self.username = username
		self.password = password
		self.email = email

	def getUsername(self):
		return self.username

	def getPassword(self):
		return self.password
	
	def getEmail(self):
		return self.email

	def getUserId(self):
		return self.user_id
	
	def addUserAnswer(self, body, problem_id, user_status):
		g.db.execute("INSERT INTO userSubs (userAnswer, problem_id, user_id, user_status) VALUES (%s, %s, %s, %s);", [body, problem_id, self.user_id, user_status])
		g.conn.commit()

	def getUserAnswer(self, problem_id):
		g.db.execute('SELECT userAnswer, user_status FROM userSubs WHERE user_id = %s and problem_id = %s;', [self.user_id, problem_id])
		user_answer = g.db.fetchone()
		if user_answer != None:
			return [user_answer['userAnswer'], user_answer['user_status']]
                return None        

	def updateUserAnswer(self, problem_id, body, user_status):
		g.db.execute("UPDATE userSubs SET userAnswer = %s, user_status = %s WHERE problem_id = %s and user_id = %s;", [body, user_status, problem_id, self.user_id])
		g.conn.commit()	

	def addUserDiff(self, problem_id, rating):
		g.db.execute("INSERT INTO userSubs (problem_id, user_id, difficulty_rating) VALUES (%s, %s, %s);", [problem_id, self.user_id, rating])
		g.conn.commit()
		g.db.execute("UPDATE problems SET difficulty_sum = difficulty_sum + %s, difficulty_votes = difficulty_votes + 1 WHERE problem_id = %s;", [rating, problem_id])
		g.conn.commit()

	def getUserDiff(self, problem_id):
		g.db.execute('SELECT difficulty_rating FROM userSubs WHERE user_id = %s and problem_id = %s;', [self.user_id, problem_id])
		user_rating = g.db.fetchone()
		if user_rating != None:
			return int(user_rating['difficulty_rating'])
                return None

	def updateUserDiff(self, problem_id, rating):
		old_rating = self.getUserDiff(problem_id)
		rating_diff = int(rating) - old_rating
		if old_rating == 0:
			vote = 1
		else:
			vote = 0
		if abs(rating_diff) > 0:
			g.db.execute("UPDATE userSubs SET difficulty_rating = %s WHERE problem_id = %s and user_id = %s;", [int(rating), problem_id, self.user_id])
			g.conn.commit()
			g.db.execute("UPDATE problems SET difficulty_sum = difficulty_sum + %s, difficulty_votes = difficulty_votes + %s WHERE problem_id = %s;", [int(rating_diff), vote, problem_id])
			g.conn.commit()
		else:
			pass

	def getProbStatus(self, problem_id):
		g.db.execute('SELECT user_status FROM userSubs WHERE user_id = %s and problem_id = %s;', [self.user_id, problem_id])
		user_status = g.db.fetchone()
		if user_status != None:
			return user_status['user_status']
                return None


	def getProbsComplete(self, category):
		g.db.execute("SELECT COUNT(u.problem_id) as complete_count FROM userSubs u JOIN problems p on u.problem_id = p.problem_id WHERE u.user_status = 'correct' and p.category = %s;", [category])
		probs = g.db.fetchone()
		return probs['complete_count']

		
