from collections import Counter
import csv
import sqlite3
import hmac

from flask import Flask, request, g, render_template, redirect, url_for

#DATABASE = '/var/www/html/flaskapp/adserver.db'
USERNAME = None
CATEGORY = ['Top', 'Bottom', 'Shoes', 'Accessory']
SELECTED = {}
for i in CATEGORY:
    SELECTED[i] = ''

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

def number_checking(s):
    # a method that checks whether the string can be converted to int or float
    try:
        int(s)
        return True
    except:
        x = s.split('.')
        if len(x) == 2:
            try:
                x0 = int(x[0])
                x1 = int(x[1])
                if x1 >= 0:
                    return True
                else:
                    return False
            except:
                return False
        else:
            return False

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        # retrive + url encoding for all fields
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        
        # check for valid entries
        if len(username) > 250:
            return render_template("signup.html",
                                   error_username='length of username > 250')
        if len(username) == 0:
            return render_template("signup.html",
                                   username=username,
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

        # hash + salt for username and password
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)

        # check for duplicated usernames
        rows = select_query("""SELECT COUNT(*) FROM user WHERE username = ?""",
                            [secured_username])
        if rows[0][0] != 0:
            return render_template("signup.html",
                                   error_username='username already exist')

        # if all correct, store the data into database and redirect to welcomeback page
        insert_query("""INSERT INTO user (username, password, bill)
                        VALUES (?,?,0)""",
                      [secured_username, secured_password])
        global USERNAME
        USERNAME = secured_username
        return redirect(url_for('welcomeback'))
    else:
        return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # retrive + url encoding for all fields
        username = request.form['username']
        password = request.form['password']
        
        # hash + salt for username and password
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)
        
        # query for the user in database
        rows = select_query("""SELECT COUNT(*) FROM user WHERE username = ? AND password = ?""",
                            [secured_username, secured_password])

        # if user exist, sent to welcomeback page. else disply error
        if rows[0][0] == 1:
            global USERNAME
            USERNAME = secured_username
            return redirect(url_for('welcomeback'))
        else:
            return render_template("login.html",
                                   username=username,
                                   error_username="user not exist or incorrect password")
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    global USERNAME
    USERNAME = None
    return redirect(url_for('index'))

@app.route('/welcomeback')
def welcomeback():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        # query information and pass them to html
        bill = select_query("""SELECT bill FROM user WHERE username = ?""",
                            [USERNAME])[0][0]
        items = select_query("""SELECT id, category, budget, min_bid,
                                max_bid, ad_url, description, current_cost
                                FROM campaign WHERE username = ? AND active = ?""",
                             [USERNAME, True])
        
        # TODO: add feature to deactative/actative the campaign on the sence

        return render_template("welcomeback.html", bill=bill, items=items)

@app.route('/newcampaign', methods=['GET', 'POST'])
def newcampaign():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        # selected help the page determine which category was selected
        # it is set to be the first item in CATEGORY by default
        if request.method == 'POST':
            category = request.form['category']
            budget = request.form['budget']
            min_bid = request.form['min_bid']
            max_bid = request.form['max_bid']
            ad_url = request.form['ad_url']
            description = request.form['description']
            
            error_budget = ""
            error_min = ""
            error_max = ""
            error_ad_url = ""

            # check errors
            if budget == "":
                error_budget = "The Budget field is empty!"
            elif not number_checking(budget):
                error_budget = "Budget is not a number!"
            else:
                budget = float(budget)
                if budget < 0:
                    error_budget = "Budget is negative!"
                    
            if min_bid == "":
                error_min = "The Minimun Bidding Price field is empty!"
            elif not number_checking(min_bid):
                error_min = "Minimun Bidding Price is not a number!"
            else:
                min_bid = float(min_bid)
                if min_bid < 0:
                    error_min = "Minimun Bidding Price is negative!"
                elif error_budget == "":
                    if min_bid > budget:
                        error_min = "Minimun Bidding Price is greater than budget!"
                    
            if max_bid == "":
                error_max = "The Maximum Bidding Price field is empty!"
            elif not number_checking(max_bid):
                error_max = "Maximum Bidding Price is not a number!"
            else:
                max_bid = float(max_bid)
                if max_bid < 0:
                    error_max = "Maximum Bidding Price is negative!"
                elif error_min == "":
                    if min_bid > max_bid:
                        error_max = "Maximum Bidding Price is less than Minimun Bidding Price !"

            if ad_url == "":
                error_ad_url = "The Ad url field is empty!"

            # NOTE: the validity of the url is not checked!!!
            # This is becasue it can be a link to another database or
            # to an image online. This part need to be specified.
            # ALSO NOTE: description field is optional by design

            if error_budget != "" or error_min != "" or error_max != "" or error_ad_url != "":
                selected = SELECTED
                selected = {category:'selected'}
                return render_template("newcampaign.html", items=CATEGORY,
                                       selected=selected, category=category,
                                       budget=budget, min_bid=min_bid,
                                       max_bid=max_bid, ad_url=ad_url,
                                       description=description,
                                       error_budget=error_budget,
                                       error_min=error_min,
                                       error_max=error_max,
                                       error_ad_url=error_ad_url)
            else:
                # insert new campaign into the database with all the defalut values
                insert_query("""INSERT INTO campaign (category, budget, min_bid,
                                max_bid, ad_url, description, total_show,
                                total_clicks, current_cost, active, username)
                                VALUES (?,?,?,?,?,?,0,0,0,?,?)""",
                             [category, budget, min_bid, max_bid, ad_url,
                              description, True,USERNAME])

                return redirect(url_for('welcomeback'))
            
        else:
            selected = SELECTED
            selected = {CATEGORY[0]:'selected'}
            
            return render_template("newcampaign.html", items=CATEGORY, selected=selected)

@app.route('/modify/<int:campaign_id>', methods=['GET', 'POST'])
def modify(campaign_id):
    # check if the user is logged in
    rows = select_query("""SELECT * FROM campaign WHERE username = ? AND id = ?""",
                        [USERNAME, campaign_id])
    if len(rows) != 1:
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            category = request.form['category']
            budget = request.form['budget']
            min_bid = request.form['min_bid']
            max_bid = request.form['max_bid']
            ad_url = request.form['ad_url']
            description = request.form['description']
            
            error_budget = ""
            error_min = ""
            error_max = ""
            error_ad_url = ""

            # check errors
            if budget == "":
                error_budget = "The Budget field is empty!"
            elif not number_checking(budget):
                error_budget = "Budget is not a number!"
            else:
                budget = float(budget)
                if budget < 0:
                    error_budget = "Budget is negative!"
                    
            if min_bid == "":
                error_min = "The Minimun Bidding Price field is empty!"
            elif not number_checking(min_bid):
                error_min = "Minimun Bidding Price is not a number!"
            else:
                min_bid = float(min_bid)
                if min_bid < 0:
                    error_min = "Minimun Bidding Price is negative!"
                elif error_budget == "":
                    if min_bid > budget:
                        error_min = "Minimun Bidding Price is greater than budget!"
                    
            if max_bid == "":
                error_max = "The Maximum Bidding Price field is empty!"
            elif not number_checking(max_bid):
                error_max = "Maximum Bidding Price is not a number!"
            else:
                max_bid = float(max_bid)
                if max_bid < 0:
                    error_max = "Maximum Bidding Price is negative!"
                elif error_min == "":
                    if min_bid > max_bid:
                        error_max = "Maximum Bidding Price is less than Minimun Bidding Price !"

            if ad_url == "":
                error_ad_url = "The Ad url field is empty!"

            # NOTE: the validity of the url is not checked!!!
            # This is becasue it can be a link to another database or
            # to an image online. This part need to be specified.
            # ALSO NOTE: description field is optional by design

            if error_budget != "" or error_min != "" or error_max != "" or error_ad_url != "":
                selected = SELECTED
                selected = {category:'selected'}
                return render_template("newcampaign.html", items=CATEGORY,
                                       selected=selected, category=category,
                                       budget=budget, min_bid=min_bid,
                                       max_bid=max_bid, ad_url=ad_url,
                                       description=description,
                                       error_budget=error_budget,
                                       error_min=error_min,
                                       error_max=error_max,
                                       error_ad_url=error_ad_url)
            else:
                # insert new campaign into the database with all the defalut values
                insert_query("""UPDATE campaign SET category = ?, budget = ?,
                                min_bid = ?, max_bid = ?, ad_url = ?,
                                description = ? WHERE username = ? and id = ?""",
                             [category, budget, min_bid, max_bid, ad_url,
                              description, USERNAME, campaign_id])

                return redirect(url_for('welcomeback'))
            
        else:
            rows = rows[0]
            selected = SELECTED
            selected = {rows[1]:'selected'}
            
            return render_template("modify.html", items=CATEGORY, selected=selected,
                                   budget=rows[2], min_bid=rows[3], max_bid=rows[4],
                                   ad_url=rows[5], description=rows[6])
@app.route('/bill')
def bill():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        return render_template("bill.html")

@app.route('/payment')
def payment():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        return render_template("payment.html")


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

