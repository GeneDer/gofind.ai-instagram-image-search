from collections import Counter
import csv
import sqlite3

from flask import Flask, request, g, render_template

DATABASE = '/var/www/html/flaskapp/natlpark.db'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POS':
        pass
    else:
        return render_template("signup.html")

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

def hello_world():
  return 'Hello from Flask!'

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=()):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return rows

if __name__ == '__main__':
  app.run()

