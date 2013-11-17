from flask import *
import pymysql
import ast
import re
from config import *
import boto
from werkzeug import secure_filename

conn = boto.connect_s3('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')



# Category class which holds list of link objects
class Category(object):
	def __init__(self, name, description, subcategories):
		self.name = name.capitalize()
		self.description = description
		if subcategories != '':
			self.subcategories = subcategories.split(',')
		else:
			self.subcategories = []


	def editSummary(self, new_description):
		g.db.execute("UPDATE categories SET description = %s WHERE title = %s;", [new_description, self.name])
		g.conn.commit()
		return


	def getLinkCount(self):
		return len(self.links)

	
	def getDescription(self):
		return self.description


	def getSubcategories(self):
		subcats = []
		for subcat in self.subcategories:
			if subcat != '':
				subcats.append(subcat)
		return subcats


	def getLinks(self, sort_type):
		cats = [self.name] + self.getSubcategories()
		format_string = ','.join(['%s'] * len(cats)) 
		links = []
		if sort_type == "rating":
			g.db.execute('SELECT l.link_id, l.title, l.description, l.url, l.category, l.content_type, round(l.rating_sum/l.rating_votes, 2) as rating, l.rating_sum, l.rating_votes, l.author_id \
                              FROM links l \
                              WHERE l.category IN (%s) ORDER BY rating DESC;' % format_string, tuple(cats))
		else:
			g.db.execute('SELECT link_id, title, description, url, category, content_type, round(rating_sum/rating_votes, 2) as rating, rating_sum, rating_votes, author_id \
                              FROM links \
                              WHERE category IN (%s) ORDER BY creation_date DESC;' % format_string, tuple(cats))
			
		db_links = g.db.fetchall()
		for link in db_links:
		     link_id = link['link_id']
		     title = link['title']
		     desc = link['description']
		     url = link['url']
		     category = link['category']
		     content_type = link['content_type']
		     rating_sum = link['rating_sum']
		     rating_votes = link['rating_votes']
		     author_id = link['author_id']
		     newLink = Link(link_id, title, desc, url, category, content_type, rating_sum, rating_votes, author_id)
		     links.append(newLink)
		return links

		
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
		g.db.execute('SELECT CONCAT(UCASE(LEFT(title,1)),SUBSTRING(title,2)) as title FROM categories;')
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
			content_type = link['content_type']
			rating_sum = link['rating_sum']
			rating_votes = link['rating_votes']
			author_id = link['author_id']
			return Link(link_id, title, desc, url, category, content_type, rating_sum, rating_votes, author_id)


	# Add a new link to the db
	def addCategory(self, title, description, parent_category, parent_subcategories):
		title = title.lower()
		g.db.execute("INSERT INTO categories (title, description) VALUES (%s, %s);", [title, description])
		g.conn.commit()
		if parent_category != None:
			if title not in parent_subcategories:
				g.db.execute("UPDATE categories SET subcategories = CONCAT(subcategories, ',', %s) WHERE title = %s;", [title, parent_category])
				g.conn.commit()
		return


	# Return a category object with list of links
	def getCategory(self, title):
		title = title.lower()
		g.db.execute('SELECT title, description, subcategories FROM categories WHERE title = %s;', [title])
		category = g.db.fetchone()
		
		if category != None:
			description = category['description']
			subcategories = category['subcategories']
			return Category(title.capitalize(), description, subcategories)
		return None



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
@application.before_request
def before_request():
	g.conn = pymysql.connect(db=DB_NAME, user=DB_USER, passwd=DB_PASSWD, host=DB_HOST)
	g.db = g.conn.cursor(pymysql.cursors.DictCursor)


# End RDS database connection after request
@application.teardown_request
def teardown_request(exception=None):
	g.conn.close()

# Link class
class Link(object):
	def __init__(self, link_id, title, desc, url, category, content_type, rating_sum, rating_votes, author_id):
		self.link_id = link_id
		self.title = title
		self.desc = desc
		self.url = url
		self.category = category
		self.content_type = content_type
		self.rating_sum = rating_sum
		self.rating_votes = rating_votes
		self.rating = self.getRating()
		self.author_id = author_id

	def getTitle(self):
		return self.title

	def getLinkId(self):
		return self.link_id

	def getDesc(self):
		return self.desc

	
	def getURL(self, clean=None):
		if clean == 'clean':
			exts = ['.com','.net','.org','.co','.io','.gov','.biz','.info','.jobs','.mobi','.name','.tel','.ca','.co.uk','.in','.cn','.br','.jp','.ru','.fr']
			for e in exts:
				if e in self.url:
					pos = self.url.index(e)
					clean = re.search(r"(?://www\.|www\.|http://|https://|https?://www\.|www\.)?((?!www\.).+)", self.url[:pos])
					return clean.group(1) + e
			return self.url
		else:
			return self.url

	def getCategory(self):
		return self.category

	def getContentType(self):
		return self.content_type

	def getRatingSum(self):
		return self.rating_sum

	def getRatingVotes(self):
		return self.rating_votes

	def getRating(self):
		return round(float(self.rating_sum)/self.rating_votes, 2)

	def getAuthorId(self):
		return self.author_id

	def getAuthorUsername(self):
		g.db.execute('select username from users where user_id = %s;', [self.author_id])
		user = g.db.fetchone()
		return user['username']

	def getCreationDate(self):
		g.db.execute("select DATE_FORMAT(creation_date,'%%M-%%d-%%Y') as date from links where link_id = %s;", [self.link_id])
		link = g.db.fetchone()
		cleanDate = link['date'].split('-')
		return cleanDate[0] + ' ' + cleanDate[1] + ', ' + cleanDate[2]




# User class
class User(object):
	def __init__(self, user_id, username, password, email):
		self.user_id = user_id
		self.username = username
		self.password = password
		self.email = email


	def uploadPhoto(self, photo):
		#filename = secure_filename(photo.filename)
		filename = str(self.user_id) + "_" + self.username + ".jpg"
		photo.save(os.path.join(UPLOAD_FOLDER, filename))
		g.db.execute("UPDATE users SET profile_pic = 'Y' WHERE user_id = %s;", [self.user_id])
		g.conn.commit()


	def hasPhoto(self):
		g.db.execute('SELECT profile_pic FROM users WHERE user_id = %s;', [self.user_id])
		db_user = g.db.fetchone()
		return db_user['profile_pic'] == 'Y'


	def getUsername(self):
		return self.username


	def getPassword(self):
		return self.password


	def getUserAbout(self):
		g.db.execute('SELECT about_me FROM users WHERE user_id = %s;', [self.user_id])
		db_links = g.db.fetchone()
		return db_links['about_me']


	def getUserJoinDate(self):
		g.db.execute("select DATE_FORMAT(join_date,'%%b-%%d-%%Y') as date from users where user_id = %s;", [self.user_id])
		link = g.db.fetchone()
		cleanDate = link['date'].split('-')
		return cleanDate[0] + ' ' + cleanDate[1] + ', ' + cleanDate[2]


	def getUserLinkCount(self):
		g.db.execute("select count(link_id) as link_count from links where author_id = %s;", [self.user_id])
		link = g.db.fetchone()
		return link['link_count']

	
	def getEmail(self):
		return self.email


	def getUserId(self):
		return self.user_id

	
	def addUserLink(self, title, desc, url, category, content_type):
		g.db.execute("INSERT INTO links (title, description, url, category, content_type, author_id) VALUES (%s, %s, %s, %s, %s, %s);", [title, desc, url, category, content_type, self.user_id])
		g.db.execute("INSERT INTO userRatings (link_id, user_id, rating, tagged) VALUES (last_insert_id(), %s, 0, 'Y');", [self.user_id])
		g.conn.commit()
		return


	def getUserLinks(self, sort_type):
		if sort_type == "rating":
			g.db.execute("SELECT l.link_id, l.title, l.description, l.url, l.category, l.content_type, round(l.rating_sum/l.rating_votes, 2) as rating, l.rating_sum, l.rating_votes, l.author_id \
                              FROM links l JOIN userRatings u on l.link_id = u.link_id  \
                              WHERE u.user_id = %s and u.tagged = 'Y' ORDER BY rating DESC;", [self.user_id])
		else:
			g.db.execute("SELECT l.link_id, l.title, l.description, l.url, l.category, l.content_type, round(l.rating_sum/l.rating_votes, 2) as rating, l.rating_sum, l.rating_votes, l.author_id \
                              FROM links l JOIN userRatings u on l.link_id = u.link_id  \
                              WHERE u.user_id = %s and u.tagged = 'Y' ORDER BY creation_date DESC;", [self.user_id])
			
		db_links = g.db.fetchall()
		links = []
		for link in db_links:
		     link_id = link['link_id']
		     title = link['title']
		     desc = link['description']
		     url = link['url']
		     category = link['category']
		     content_type = link['content_type']
		     rating_sum = link['rating_sum']
		     rating_votes = link['rating_votes']
		     author_id = link['author_id']
		     newLink = Link(link_id, title, desc, url, category, content_type, rating_sum, rating_votes, author_id)
		     links.append(newLink)
		return links
                

	def updateUserLink(self, link_id, title, description, url, category, content_type):
		g.db.execute("UPDATE links SET title = %s, description = %s, url = %s, category = %, content_type = %s  WHERE link_id = %s;", [title, description, url, category, content_type, link_id])
		g.conn.commit()	


	def updateProfile(self, about_me):
		g.db.execute("UPDATE users SET about_me = %s WHERE user_id = %s;", [about_me, self.user_id])
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
			g.db.execute("UPDATE userRatings SET rating = %s WHERE link_id = %s and user_id = %s;", [int(new_rating), link_id, self.user_id])
			g.conn.commit()
			g.db.execute("UPDATE links SET rating_sum = rating_sum + %s, rating_votes = rating_votes + %s WHERE link_id = %s;", [int(rating_diff), vote, link_id])
			g.conn.commit()
		else:
			pass		


	def tagLink(self, link_id, tag_type):
		user_rating = self.getUserRating(link_id)
		if user_rating != None:
			g.db.execute("UPDATE userRatings SET tagged = %s WHERE link_id = %s and user_id = %s;", [tag_type, link_id, self.user_id])
			g.conn.commit()	
		else:
			g.db.execute("INSERT INTO userRatings (link_id, user_id, rating, tagged) VALUES (%s, %s, 0, %s);", [link_id, self.user_id, tag_type])
			g.conn.commit()	


	def taggedStatus(self, link_id):
		g.db.execute("SELECT tagged FROM userRatings WHERE link_id = %s and user_id = %s;", [link_id, self.user_id])
		link = g.db.fetchone()
		if link == None:
			return 'N'
		else:
			return link['tagged']

