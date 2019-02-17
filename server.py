from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL

import re
from flask_bcrypt import Bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "eatmyshorts!"
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/register', methods=['POST'])
def register():
    # validations
    error = False
    # checks to make sure the first name is more than 2 chars
    if len(request.form['first_name']) < 2:
        flash("WRONG! FIRST NAME MUST BE 2 OR MORE CHARACTERS")
        error = True
    # checks to see if the last name is grtr than 2 chars
    if len(request.form['last_name']) < 2:
        flash("LOLOL! LAST NAME MUST BE 2 OR MORE CHARACTERS")
        error = True
    # checks to see that the password is longer than 7 chars
    if len(request.form['password']) < 8:
        flash("WTF IS WRONG WITH YOU! PASSWORD MUST BE LONGER THAN 7 CHARACTERS")
        error = True
    # checks that the PW and CPW match
    if request.form['password'] != request.form['c_password']:
        flash("PASSWORDS MUST MATCH, IDIOT")
        error = True
    # checks that only alphabet letters were entered
    if not request.form['first_name'].isalpha():
        flash("NO BOTS OR PEOPLE WHO IDENTIFY AS BOTS WELCOME")
        error = True
    # checks that only alphabet letters were entered
    if not request.form['last_name'].isalpha():
        flash("NO BOTS ALLOWED HERE, BOT-MAN")
        error = True
    # makes sure that only email syntax was entered
    if not EMAIL_REGEX.match(request.form['email']):
        flash("BOTS NOT WELCOME, TRY twitter.com INSTEAD")
        error = True
    # query to make sure there are no mathcing emails in the db
    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('quotesDB')
    matching_email_users = mysql.query_db(query,data)
    if len(matching_email_users) > 0:
        flash("Identity theft is funny...JK, IT IS NOT FUNNY...GO AWAY")
        error = True
    if error:
        return redirect('/')

    # query to create a new user and add them to db
    data = {
        "first_name" : request.form['first_name'],
        "last_name"  : request.form['last_name'],
        "email"      : request.form['email'],
        "password"   : bcrypt.generate_password_hash(request.form['password'])
    }
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, NOW(), NOW());"
    mysql = connectToMySQL('quotesDB')
    user_id = mysql.query_db(query, data)
    session['user_id'] = user_id
    return redirect('/')
    print(user_id)

@app.route('/login', methods=['POST'])
def login():
    # query to compare the email entered into the form vs what's in the DB
    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('quotesDB')
    matching_email_users = mysql.query_db(query,data)
    # checks to see if the email already exists in the DB
    if len(matching_email_users) == 0:
        flash("Nice try Wise-Guy")
        print("bad email")
        return redirect('/')
    user = matching_email_users[0]
    # if the stored PW is the same as the password entered, continue to next page
    if bcrypt.check_password_hash(user['password'], request.form['password']):
        session['user_id'] = user['id']
        return redirect('/quotes')
    flash("Invalid credentials...admins have alerted the FBI")
    print("bad pw")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#takes you back to quotes page
@app.route('/back')
def back():
    return redirect('/quotes')

# displays main page
@app.route('/quotes')
def quotes():
	if not 'user_id' in session:
		flash("Get out!")
		return redirect('/')
	# query to get logged in users first and last name
	data={
		"user_id": session['user_id']
	}
	query="SELECT * FROM users WHERE id= %(user_id)s;"
	mysql=connectToMySQL('quotesDB')
	user=mysql.query_db(query, data)
	# query to get all quotes created by other users along with the users first and last name from the users table
	query="SELECT * FROM quotes JOIN users on users.id= quotes.creator_id WHERE creator_id != %(user_id)s;"
	mysql=connectToMySQL('quotesDB')
	other_quotes=mysql.query_db(query, data)
	# query to get all quotes created by logged in user
	query="SELECT * FROM quotes WHERE creator_id = %(user_id)s;"
	mysql=connectToMySQL('quotesDB')
	my_quotes=mysql.query_db(query, data)
	return render_template('dashboard.html', user=user[0], other_quotes=other_quotes, my_quotes=my_quotes )

# displays the creators quotes
@app.route('/user/<int:creator_id>')
def creator(creator_id):
	data={
		"creator_id": creator_id
	}
	# query to get the creators first name and last name
	query="SELECT * FROM quotes LEFT JOIN users ON users.id= quotes.creator_id WHERE quotes.creator_id = %(creator_id)s;"
	mysql=connectToMySQL('quotesDB')
	creator=mysql.query_db(query, data)
	# query to get the creators quotes
	query="SELECT * FROM quotes WHERE creator_id=%(creator_id)s;"
	mysql=connectToMySQL('quotesDB')
	quotes=mysql.query_db(query, data)
	return render_template('userquotes.html', creator=creator[0], quotes=quotes)

# deletes a quote based off of quote id
@app.route('/delete/<int:quote_id>')
def delete(quote_id):
	data={
		"quote_id": quote_id
	}
	query="DELETE FROM quotes WHERE id = %(quote_id)s;"
	mysql=connectToMySQL('quotesDB')
	mysql.query_db(query, data)
	return redirect('/quotes')

# query adds a quote into db, quotes table
@app.route('/add/<int:user_id>', methods=['POST'])
def add(user_id):
	# validations/ author more than 3 chars
	error= False
	if len(request.form['author']) < 3:
		flash("Author's name must be more than 3 characters")
		error= True
	#  val/ content more than 10 chars 
	if len(request.form['content']) < 10:
		flash("Quote must be more than 10 characters")
		error= True
	if error:
		return redirect('/quotes')

	data={
		"creator_id": session["user_id"],
		"author": request.form['author'],
		"content": request.form['content']
	}
	query="INSERT INTO quotes(creator_id, author, content, created_at, updated_at) VALUES(%(creator_id)s, %(author)s, %(content)s, NOW(), NOW());"
	mysql=connectToMySQL('quotesDB')
	mysql.query_db(query,data)
	return redirect('/quotes')

# displays edit page with logged in users name and email
@app.route('/myaccount/<int:user_id>')
def editUser(user_id):
	
	data={
		"user_id": session['user_id']
	}
	query="SELECT * FROM users WHERE id= %(user_id)s;"
	mysql=connectToMySQL('quotesDB')
	user=mysql.query_db(query,data)
	return render_template("edit.html", user=user[0])
	

@app.route('/update/<int:user_id>', methods=['POST'])
def edit(user_id):
	# validations
	error = False
	if len(request.form['first_name']) < 1:
		flash("First name is EMPTY")
		error= True
	if len(request.form['last_name']) < 1:
		flash("LAST NAME IS EMPTY")
		error= True
	if len(request.form['email']) < 1:
		flash("Email is EMPTY")
		error= True
	if not request.form['first_name'].isalpha():
		flash("ONLY LETTERS DUDE")
		error= True
	if not request.form['last_name'].isalpha():
		flash("ONLY LETTERS DUDE")
		error= True

	if not EMAIL_REGEX.match(request.form['email']):
		flash("INPUT A REAL EMAIL")
		error= True
	# query to get users email
	data={
		"user_id": session['user_id']
	}
	query="SELECT email FROM users WHERE id = %(user_id)s;"
	mysql = connectToMySQL('quotesDB')
	user_email = mysql.query_db(query,data)
	# validate email for matching emails if users email is different
	if not request.form['email'] == user_email:
		data = {
		    "email" : request.form['email'],
		    "user_id": session['user_id']
		}
		query = "SELECT * FROM users WHERE email = %(email)s"
		mysql = connectToMySQL('quotesDB')
		matching_email_users = mysql.query_db(query,data)

		if len(matching_email_users) > 0:
			flash("THIS EMAIL ALREADY EXISTS!")
			error = True
	
	if error:
	    return redirect('/myaccount/'+ str(session['user_id']))
	
	# query to update the logged in users first name, last name, and email
	data={
		"first_name": request.form['first_name'],
		"last_name": request.form['last_name'],
		"email": request.form['email'],
		"user_id": session['user_id']
	}
	query="UPDATE users SET first_name= %(first_name)s, last_name= %(last_name)s, email= %(email)s WHERE id = %(user_id)s;"
	mysql = connectToMySQL('quotesDB')
	mysql.query_db(query,data)
	return redirect('/quotes')

if __name__ == "__main__":
    app.run(debug=True)





