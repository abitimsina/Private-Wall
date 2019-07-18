from flask import Flask, render_template, redirect, flash, request, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "It's Secret"
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')





@app.route("/")
def display():
    return render_template("index.html")




@app.route("/process", methods=["POST"])
def register():
    is_valid = True
    if len(request.form['firstname']) < 2:
        is_valid = False
        flash("Please enter first name with more than 2 characters")

    if len(request.form['lastname']) < 2:
        is_valid = False
        flash("Please enter a last name with more than 2 characters")

    if not EMAIL_REGEX.match(request.form["email"]):
        flash("Invalid Email")

    else:
        mysql = connectToMySQL("wall_re")
        query = "SELECT * FROM user WHERE email = %(em)s"
        data = {
            "em": request.form["email"]
        } 
        result = mysql.query_db(query, data)
        if len(result) != 0:
            flash("Account already exists!")
            return redirect("/")

    if len(request.form["password"]) < 9:
        is_valid = False
        flash("Password must have more than 9 characters")
        return redirect("/")

    if request.form["password"] != request.form["password_confirm"]:
        flash("Password must match!")
        return redirect("/")


    else:
        pw_hash = bcrypt.generate_password_hash(request.form["password"])
        mysql = connectToMySQL("wall_re")
        query = "INSERT INTO user(first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(password_hash)s, NOW(), NOW());"
        data = {
            "fn": request.form["firstname"],
            "ln": request.form["lastname"],
            "em": request.form["email"],
            "password_hash": pw_hash
        }
        mysql.query_db(query, data)
        flash("Your email is successfully created")
        return redirect("/")







@app.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL("wall_re")
    query = "SELECT * FROM user WHERE email = %(em)s;"
    data = {
        "em": request.form["email"]
    }
    result = mysql.query_db(query, data)
    if result:
        	if bcrypt.check_password_hash(result[0]["password"], request.form["password"]):
        		session["user_id"] = result[0]["id"]
        		return redirect ("/success")
    flash("Cannot log in!")
    return redirect("/")







@app.route("/success")
def succcess():
    if "user_id" not in session:
        flash("You need to be logged in to view this page!")
        return redirect("/")
    else:
        db = connectToMySQL("wall_re")
        query = "SELECT * FROM user ORDER BY first_name;"
        send_message = db.query_db(query)
        db = connectToMySQL("wall_re")
        query = "SELECT user.id, user.first_name, messages.id, messages.recepient_id, messages.messages, messages.created_at FROM user JOIN messages ON user.id = messages.user_id WHERE recepient_id = %(rid)s;"
        
        data = {
            "rid": session["user_id"]
        }
        messages = db.query_db(query, data)



        messages_total = len(messages)
        db = connectToMySQL("wall_re")
        query= "SELECT COUNT(*) FROM messages WHERE user_id = %(id)s;"
        data = {
            "id": session["user_id"]
        }
        sent = db.query_db(query, data)


        db = connectToMySQL("wall_re")
        query = "SELECT * FROM user WHERE id = %(id)s;"
        data = {
            "id": session["user_id"],
        }
        users = db.query_db(query, data)


    return render_template("welcome.html", messages = messages, send_message = send_message, all_sent = sent, messages_total = messages_total, all_users = users)






@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out!!")
    return redirect("/")







@app.route('/messages', methods = ['POST'])
def messages():
	if len(request.form['message']) < 5:
		flash('Say something of value')
		return redirect('/success')
	else:
		db = connectToMySQL('wall_re')
		query = 'INSERT INTO messages (user_id, recepient_id, messages) VALUES (%(uid)s, %(ri)s, %(m)s);'
		data = {
		'uid': session['user_id'],
		'ri': request.form['recepient_id'],
		'm': request.form['message']
		}
		db.query_db(query, data)
		print(request.form)
		return redirect('/success')






@app.route('/delete/<id>')
def delete(id):
	db = connectToMySQL('wall_re')
	query = 'DELETE FROM messages WHERE id = %(id)s;'
	data = {
	'id': id,
	}
	db.query_db(query, data)
	return redirect('/success')




if __name__=="__main__":
    app.run(debug=True)