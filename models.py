from flask import *
import pymysql
import ast
import re
from config import *



# Category class which holds list of link objects
class Category(object):
	def __init__(self, name):
		self.name = name
		self.links = self.genLinkList()

	def getLinkCount(self):
		return len(self.links)

	def genLinkList(self, order="DESC"):
		links = []
		g.db.execute('SELECT link_id, title, description, url, category, ROUND(rating_sum/rating_votes,2) as rating, rating_votes, username  
                              FROM links l JOIN users u on u.user_id = l.author_id
                              WHERE category = %s ORDER BY rating DESC;', [self.name])
		links = g.db.fetchall()
		for link in links:
		     link_id = link['link_id']
		     title = link['title']
		     desc = link['description']
		     category = link['category']
		     category_position = 1
		     rating = link['rating']
		     rating_votes = link['rating_votes']
		     username = link['username']
		     newLink = Link(link_id, title, desc, self.name, category_position, rating, rating_votes, username)
		     links.append(newLink)
		return links
		
	def getLinks(self):
		return self.links

	def getCategoryName(self):
		return self.name



# Application class which includes high level functions to manipulate User and Link instances
class App(object):
	def __init__(self):
		self.application = Flask(__name__)
		self.secret_key = 'secret2222'

	# Return number of unique links in database
	def getLinkCount(self, category=None):
		if category != None:
			g.db.execute('select count(link_id) as link_count FROM links WHERE category = %s', [category])
		else:
			g.db.execute('select count(link_id) as link_count FROM links')
		link = g.db.fetchone()
		return link['link_count']


	# Returns list of link titles in database
	def getLinkTitles(self):
		g.db.execute("SELECT title FROM links")
		title_list = g.db.fetchall()
		return title_list
	


	# Returns list of categories 
	def getCategories(self):
		g.db.execute('SELECT category, count(link_id) as link_count, MIN(link_id) as min_link_id FROM links GROUP BY category ORDER BY count(link_id) DESC;')
		categories = g.db.fetchall()
		return categories


	# Returns a list with [link position in category, length of category] 
	def getCategoryPosition(self, link_id, category):
		g.db.execute('SELECT COUNT(CASE WHEN link_id < %s THEN link_id ELSE NULL END) + 1 as current_link, count(link_id) as total_links FROM links WHERE category = %s ORDER BY link_id ASC;', [link_id, category])
		link = g.db.fetchone()
		return link

	
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


	# Add a new link to the db
	def addLink(self, title, desc, url, category, author_id):
		g.db.execute("INSERT INTO links (title, description, url, category, author_id) VALUES (%s, %s, %s, %s, %s);", [title, desc, url, category, author_id])
		g.conn.commit()

		g.db.execute('SELECT * FROM links WHERE title = %s;', [title])
		link = g.db.fetchone()
		link_id = link['link_id']
		rating_sum = link['rating_sum']
		rating_votes = link['rating_votes']
		return Link(link_id, title, desc, url, category, rating_sum, rating_votes, author_id)

	
	# Return a link object to the user
	def getLink(self, link_id):
		g.db.execute('SELECT * FROM links WHERE link_id = %s;', [link_id])
		link = g.db.fetchone()
		if link == None:
			return None
		else:
			link_id = link['link_id']
			title = link['title']
			desc = link['description']
			url = link['url']
			category = link['category']
			rating_sum = link['rating_sum']
			rating_votes = link['rating_votes']
			author_id = link['author_id']
			return Link(link_id, title, desc, url, category, rating_sum, rating_votes, author_id)



	# Return a category object with list of links
	def getCategory(self, name):
		return Category(name)
	



	# Return the next or previous link in the same category
	def getNextLink(self, link_id, category, direction):
		if direction == 'next':
			g.db.execute('select min(link_id) as new_link_id from links where link_id > %s and category = %s ;', [link_id, category])
			nextLink = g.db.fetchone()
			if nextLink['new_link_id'] != None:
				next_link_id = nextLink['new_link_id']
			else:
				g.db.execute('select min(link_id) as new_link_id from links where category = %s;', [category])
				nextLink = g.db.fetchone()
				next_link_id = nextLink['new_link_id']
		else:
			g.db.execute('select max(link_id) as new_link_id from links where link_id < %s and category = %s ;', [link_id, category])
			nextLink = g.db.fetchone()
			if nextLink['new_link_id'] != None:
				next_link_id = nextLink['new_link_id']
			else:
				g.db.execute('select min(link_id) as new_link_id from links where category = %s;', [category])
				nextLink = g.db.fetchone()
				next_link_id = nextLink['new_link_id']
		return next_link_id


	# Return a random link in the same category
	def getRandomLink(self, problem_id, category):
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
@application.before_request                                                                                                                                                                      def before_request():                                                                                                                                                                    
    g.conn = pymysql.connect(db=DB_NAME, user=DB_USER, passwd=DB_PASSWD, host=DB_HOST)
    g.db = g.conn.cursor(pymysql.cursors.DictCursor)
    #g.conn = pymysql.connect(db='test', unix_socket='/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock', user='root', passwd='')                                                          


# End RDS database connection after request                                                                                                                                                  
@application.teardown_request                                                                                                                                                                    def teardown_request(exception=None):                                                                                                                                                                 	g.conn.close()   


# Link class
class Link(object):
	def __init__(self, link_id, title, desc, url, category, rating_sum, rating_votes, author_id):
		self.link_id = link_id
		self.title = title
		self.desc = desc
		self.url = url
		self.category = category
		self.rating_sum = rating_sum
		self.difficulty_votes = rating_votes
		self.rating = self.getRating()
		self.author_id

	def getTitle(self):
		return self.title

	def getLinkId(self):
		return self.link_id

	def getDesc(self):
		return self.desc

	def getURL(self):
		return self.url

	def getCategory(self):
		return self.category

	def getRatingSum(self):
		return self.rating_sum

	def getRatingVotes(self):
		return self.rating_votes

	def getRating(self):
		return round(float(self.rating_sum)/rating_votes, 2)

	def getAuthorId(self):
		return self.author_id



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
	
	def addUserLink(self, title, desc, url, category):
		g.db.execute("INSERT INTO links (title, description, url, category, author_id) VALUES (%s, %s, %s, %s, %s);", [title, desc, url, category, self.user_id])
		g.conn.commit()

	def getUserLinks(self, link_id):
		g.db.execute('SELECT * FROM links WHERE author_id = %s;', [self.user_id])
		user_links = g.db.fetchall()
                return user_links        

	def updateUserLink(self, link_id, title, description, url, category):
		g.db.execute("UPDATE links SET title = %s, description = %s, url = %s, category = % WHERE link_id = %s;", [title, description, url, category, link_id])
		g.conn.commit()	

	def addUserRating(self, link_id, rating):
		g.db.execute("INSERT INTO userRatings (link_id, user_id, rating) VALUES (%s, %s, %s);", [link_id, self.user_id, rating])
		g.conn.commit()
		g.db.execute("UPDATE links SET rating_sum = rating_sum + %s, rating_votes = rating_votes + 1 WHERE link_id = %s;", [rating, link_id])
		g.conn.commit()

	def getUserRating(self, link_id):
		g.db.execute('SELECT rating FROM userRatings WHERE user_id = %s and link_id = %s;', [self.user_id, link_id])
		user_rating = g.db.fetchone()
		if user_rating != None:
			return int(user_rating['rating'])
                return None

	def updateUserRating(self, link_id, new_rating):
		old_rating = self.getUserRating(link_id)
		rating_diff = int(new_rating) - old_rating
		if old_rating == 0:
			vote = 1
		else:
			vote = 0
		if abs(rating_diff) > 0:
			g.db.execute("UPDATE userLinks SET rating = %s WHERE link_id = %s and user_id = %s;", [int(new_rating), link_id, self.user_id])
			g.conn.commit()
			g.db.execute("UPDATE links SET rating_sum = rating_sum + %s, rating_votes = rating_votes + %s WHERE link_id = %s;", [int(rating_diff), vote, link_id])
			g.conn.commit()
		else:
			pass		
