from collections import Counter
import csv
import sqlite3
import hmac
import random
import time

from flask import Flask, request, g, render_template, redirect, url_for, jsonify, abort
from flask import session as login_session


#DATABASE = '/var/www/html/flaskapp/adserver.db'
RANDOM_AD_PROB = 0.2
EXPIRED_REQUEST_TIME = 3600
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
    # a method that checks whether the string can be
    # converted to either int or float
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
    if 'username' in login_session:
        return redirect(url_for('welcomeback'))
    else:
        return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        # retrive for all fields
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

        # if all correct, store the data into database
        # and redirect to welcomeback page
        insert_query("""INSERT INTO user (username, password, bill)
                        VALUES (?,?,0)""",
                      [secured_username, secured_password])
        login_session['username'] = secured_username
        return redirect(url_for('welcomeback'))
    else:
        return render_template("signup.html")

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # retrive + url encoding for all fields
        username = request.form['username']
        password = request.form['password']
        
        # hash + salt for username and password
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)
        
        # query for the user in database
        rows = select_query("""SELECT COUNT(*) FROM user
                               WHERE username = ? AND password = ?""",
                            [secured_username, secured_password])

        # if user exist, sent to welcomeback page. else disply error
        if rows[0][0] == 1:
            login_session['username'] = secured_username
            return redirect(url_for('welcomeback'))
        else:
            return render_template("login.html",
                                   error="user does not exist or incorrect password")
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    login_session.pop('username')
    return redirect(url_for('index'))

@app.route('/welcomeback')
def welcomeback():
    # check if the user is logged in
    if 'username' not in login_session:
        return redirect(url_for('index'))
    else:
        # query information and pass them to html
        bill = select_query("""SELECT bill FROM user WHERE username = ?""",
                            [login_session['username']])[0][0]
        items1 = select_query("""SELECT id, category, budget, min_bid,
                                 max_bid, ad_url, description, current_cost
                                 FROM campaign WHERE username = ? AND active = ?""",
                              [login_session['username'], True])

        items2 = select_query("""SELECT id, category, budget, min_bid,
                                 max_bid, ad_url, description, current_cost
                                 FROM campaign WHERE username = ? AND active = ?""",
                              [login_session['username'], False])
        
        return render_template("welcomeback.html", bill=float(bill), items1=items1, items2=items2)

@app.route('/newcampaign', methods=['GET', 'POST'])
def newcampaign():
    # check if the user is logged in
    if 'username' not in login_session:
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
                              description, True, login_session['username']])

                return redirect(url_for('welcomeback'))
            
        else:
            selected = SELECTED
            selected = {CATEGORY[0]:'selected'}
            
            return render_template("newcampaign.html", items=CATEGORY, selected=selected)

@app.route('/modify/<int:campaign_id>', methods=['GET', 'POST'])
def modify(campaign_id):
    # check if the user is logged in
    rows = select_query("""SELECT * FROM campaign WHERE username = ? AND id = ?""",
                        [login_session['username'], campaign_id])
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
                # update the campaign in the database with new values
                insert_query("""UPDATE campaign SET category = ?, budget = ?,
                                min_bid = ?, max_bid = ?, ad_url = ?,
                                description = ? WHERE username = ? and id = ?""",
                             [category, budget, min_bid, max_bid, ad_url,
                              description, login_session['username'], campaign_id])

                return redirect(url_for('welcomeback'))
            
        else:
            rows = rows[0]
            selected = SELECTED
            selected = {rows[1]:'selected'}
            
            return render_template("modify.html", items=CATEGORY, selected=selected,
                                   budget=rows[2], min_bid=rows[3], max_bid=rows[4],
                                   ad_url=rows[5], description=rows[6])

@app.route('/active/<int:campaign_id>/<int:redirect_id>')
def active(campaign_id, redirect_id):
    # check if the user is logged in
    rows = select_query("""SELECT * FROM campaign WHERE username = ? AND id = ?""",
                        [login_session['username'], campaign_id])
    if len(rows) != 1:
        return redirect(url_for('index'))
    else:
        # active the campaign
        insert_query("""UPDATE campaign SET active = ?
                        WHERE username = ? and id = ?""",
                     [True, login_session['username'], campaign_id])

        if redirect_id == 1:
            return redirect(url_for('welcomeback'))
        else:
            return redirect(url_for('bill'))

@app.route('/deactive/<int:campaign_id>/<int:redirect_id>')
def deactive(campaign_id, redirect_id):
    # check if the user is logged in
    rows = select_query("""SELECT * FROM campaign WHERE username = ? AND id = ?""",
                        [login_session['username'], campaign_id])
    if len(rows) != 1:
        return redirect(url_for('index'))
    else:
        # active the campaign
        insert_query("""UPDATE campaign SET active = ?
                        WHERE username = ? and id = ?""",
                     [False, login_session['username'], campaign_id])
        if redirect_id == 1:
            return redirect(url_for('welcomeback'))
        else:
            return redirect(url_for('bill'))

@app.route('/bill')
def bill():
    # check if the user is logged in
    if 'username' not in login_session:
        return redirect(url_for('index'))
    else:
        # query information and pass them to html
        bill = select_query("""SELECT bill FROM user WHERE username = ?""",
                            [login_session['username']])[0][0]
        items = select_query("""SELECT id, budget, total_show, total_clicks,
                                current_cost, active
                                FROM campaign WHERE username = ?
                                AND current_cost >= 0""",
                             [login_session['username']])

        return render_template("bill.html", bill=float(bill), items=items)

@app.route('/payment')
def payment():
    # check if the user is logged in
    if 'username' not in login_session:
        return redirect(url_for('index'))
    else:
        return render_template("payment.html")


# ad request api's
@app.route('/ad_request/<username>/<password>/<catogory>')
def ad_request(username, password, catogory):

    ####################################
    # for testing purpose only, mack sure to remove the hashing
    rows = select_query("""SELECT COUNT(*) FROM customer WHERE username = ?
                           AND password = ?""",
                        [make_secure_username(username),
                         make_secure_password(password)])
    ####################################
    
    request_id = None
    request_key = None
    request_url = None
    request_bid = None
    request_show = None
    # if customer exist, check for the available campaign
    if rows[0][0] == 1 and catogory in CATEGORY:
        max_bids = select_query("""SELECT max_bid, count(*)
                                   FROM campaign
                                   WHERE category = ? AND active = ?
                                   GROUP BY max_bid
                                   ORDER BY max_bid DESC
                                   LIMIT 2""",
                                    [catogory, True])

        # if there are campaigns in this category
        if len(max_bids) > 0:

            # give a random ad at RANDOM_AD_PROB of time
            if random.random() > RANDOM_AD_PROB:
                winner = select_query("""SELECT id, ad_url, total_show, max_bid
                                         FROM campaign
                                         WHERE category = ? AND active = ?
                                         ORDER BY RAND()
                                         LIMIT 1""",
                                      [catogory, True])
                request_bid = winner[0][3]

            # do the actual bidding otherwise
            else:

                # if more than one campaign with highest bid,
                if max_bids[0][1] > 1:
                    # randomly select one highest bid as the winner
                    winner = select_query("""SELECT id, ad_url, total_show
                                             FROM campaign
                                             WHERE category = ? AND active = ?
                                             AND max_bid = ?
                                             ORDER BY RAND()
                                             LIMIT 1""",
                                          [catogory, True, max_bids[0][0]])
                    request_bid = max_bids[0][0]

                # if there are only one campaign
                elif len(max_bids) == 1:
                    # only one active campaign, just return the min_bid
                    winner = select_query("""SELECT id, ad_url, total_show, min_bid
                                             FROM campaign
                                             WHERE category = ? AND active = ?
                                             AND max_bid = ?""",
                                          [catogory, True, max_bids[0][0]])
                    request_bid = winner[0][3]

                # else its the case for one highest bidder and some second bidders
                else:
                    # only one active campaign with highest bid, just return
                    # max(min_bid of the selected bid, second highest bid)
                    winner = select_query("""SELECT id, ad_url, total_show, min_bid
                                             FROM campaign
                                             WHERE category = ? AND active = ?
                                             AND max_bid = ?""",
                                          [catogory, True, max_bids[0][0]])
                    request_bid = max(winner[0][3], max_bids[1][0] + 0.01)

            # all of them are setting id, url, show, and key the same way
            request_id = winner[0][0]
            request_url = winner[0][1]
            request_show = winner[0][2] + 1
            request_key = random.randint(-2000000000, 2000000000)
        
            # update total show and add it to the ad_reques
            insert_query("""UPDATE campaign
                            SET total_show = ?
                            WHERE id = ?""",
                         [request_show, request_id])
            
            insert_query("""INSERT INTO ad_request
                            (request_key, campaign_id, bid_price, timestamp)
                            VALUES (?, ?, ?, ?)""",
                         [request_key, request_id, request_bid, time.time()])        

    return jsonify({'id': request_id, 'key': request_key, 'url': request_url})

@app.route('/ad_passes/<request_id>/<random_key>')
def ad_passes(request_id, random_key):
    
    # get bid price
    bid_price = select_query("""SELECT bid_price
                                FROM ad_request
                                WHERE campaign_id = ?
                                AND request_key = ?""",
                             [request_id, random_key])
    
    # if campaign_id exist, update bill, total_click, and current_cost
    if bid_price:
        campaign_info = select_query("""SELECT budget, max_bid,
                                        total_clicks, current_cost,
                                        username
                                        FROM campaign
                                        WHERE id = ?""",
                                     [request_id])
        insert_query("""UPDATE user
                        SET bill = bill + ?
                        WHERE username = ?""",
                     [bid_price[0][0],
                      campaign_info[0][4]])

        # check for the budget and set campaign inactivate if not enough money
        current_cost = campaign_info[0][3] + bid_price[0][0]
        if current_cost + campaign_info[0][1] > campaign_info[0][0]:
            insert_query("""UPDATE campaign
                            SET total_clicks = ?,
                            current_cost = ?,
                            active = ?
                            WHERE id = ?""",
                         [campaign_info[0][2] + 1,
                          campaign_info[0][3] + bid_price[0][0],
                          request_id, False])
        else:
            insert_query("""UPDATE campaign
                            SET total_clicks = ?,
                            current_cost = ?
                            WHERE id = ?""",
                         [campaign_info[0][2] + 1,
                          campaign_info[0][3] + bid_price[0][0],
                          request_id])

    # delete this ad request and expired requests
    insert_query("""DELETE FROM ad_request
                    WHERE campaign_id = ? AND request_key = ?
                    OR timestamp < ?""",
                 [request_id, random_key, time.time() - EXPIRED_REQUEST_TIME])
    
    return jsonify("action complete")

@app.route('/ad_fails/<request_id>/<random_key>')
def ad_fails(request_id, random_key):

    # delete this ad request and expired requests
    insert_query("""DELETE FROM ad_request
                    WHERE campaign_id = ? AND request_key = ?
                    OR timestamp < ?""",
                 [request_id, random_key, time.time() - EXPIRED_REQUEST_TIME])
    return jsonify("action complete")
    
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

if __name__ == '__main__':
    app.secret_key = 'osjfodiasjoIHUUYoihiuGhiUYgUTf%^^7Y9*hOIlBgCHFyTFu&%T'
    app.run(threaded=True)

