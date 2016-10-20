from collections import Counter
import csv
import sqlite3
import urllib
import hmac

from flask import Flask, request, g, render_template, redirect, url_for

#DATABASE = '/var/www/html/flaskapp/adserver.db'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    #return sqlite3.connect(app.config['DATABASE'])
    return sqlite3.connect('adserver.db')

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

secret1 = "GeneDerSu@gofind.ai-0912u90jds"
secret2 = "lmcxvlcxm10-980ucvjn2l3mrec0jl"
def make_secure_username(val):
    return hmac.new(secret1, val).hexdigest()
def make_secure_password(val):
    return hmac.new(secret2, val).hexdigest()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = urllib.quote_plus(request.form['username'])
        password = urllib.quote_plus(request.form['password'])
        verify = urllib.quote_plus(request.form['verify'])
        
        # checking for valid entries
        if len(username) > 250:
            return render_template("signup.html",
                                   error_username='length of username > 250')
        if len(username) == 0:
            return render_template("signup.html",
                                   username=urllib.unquote_plus(username),
                                   error_username='no username entered')
        if len(password) > 250:
            return render_template("signup.html",
                                   error_password='length of password > 250')
        if len(password) == 0:
            return render_template("signup.html",
                                   error_password='no password entered')
        if password != verify:
            return render_template("signup.html",
                                   error_varify='passwords do not match')
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)
        rows = select_query("""SELECT COUNT(*) FROM user WHERE username = ?""",
                            [secured_username])
        print "hello:", rows, len((secured_username, secured_password))
        if rows[0][0] != 0:
            return render_template("signup.html",
                                   error_username='username already exist')

        insert_query("""INSERT INTO user (username,password) VALUES (?,?)""",
                      [secured_username, secured_password])

        return redirect(url_for('welcomeback'))
    else:
        return render_template("signup.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/welcomeback')
def welcomeback():
    return render_template("welcomeback.html")

@app.route('/modify')
def modify():
    return render_template("modify.html")

@app.route('/newcampaign')
def newcampaign():
    return render_template("newcampaign.html")

@app.route('/payment')
def payment():
    return render_template("payment.html")

@app.route('/bill')
def bill():
    return render_template("bill.html")


@app.route('/countme/<input_str>')
def count_me(input_str):
    input_counter = Counter(input_str)
    response = []
    for letter, count in input_counter.most_common():
        response.append('"{}": {}'.format(letter, count))
    return '<br>'.join(response)

@app.route("/viewdb")
def viewdb():
    rows = execute_query("""SELECT * FROM natlpark""")
    return '<br>'.join(str(row) for row in rows)

@app.route("/state/<state>")
def sortby(state):
    rows = execute_query("""SELECT * FROM natlpark WHERE state = ?""",
                         [state.title()])
    return '<br>'.join(str(row) for row in rows)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def select_query(query, args=()):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return rows

def insert_query(query, args=()):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()
    conn.close()

if __name__ == '__main__':
  app.run()

