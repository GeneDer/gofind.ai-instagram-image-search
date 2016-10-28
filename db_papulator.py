import sqlite3
import hmac

# connect to database
conn = sqlite3.connect('adserver.db')
cur = conn.cursor()

# hashing username and password
secret1 = "GeneDerSu@gofind.ai-0912u90jds"
secret2 = "lmcxvlcxm10-980ucvjn2l3mrec0jl"
def make_secure_username(val):
    return hmac.new(secret1, val).hexdigest()
def make_secure_password(val):
    return hmac.new(secret2, val).hexdigest()

# add 2 users
cur.execute("""INSERT INTO user
               (username, password, bill)
               VALUES (?,?,0)""",
            [make_secure_username('111'), make_secure_password('111')])

cur.execute("""INSERT INTO user
               (username, password, bill)
               VALUES (?,?,0)""",
            [make_secure_username('222'), make_secure_password('222')])

# add 3 campaigns
cur.execute("""INSERT INTO campaign (category, budget, min_bid,
               max_bid, ad_url, description, total_show,
               total_clicks, current_cost, active, username)
               VALUES (?,?,?,?,?,?,0,0,0,?,?)""",
            ('Top', 10, 1, 3, 'xxx.yyy.zzz', 'test1', True,
             make_secure_username('111')))

cur.execute("""INSERT INTO campaign (category, budget, min_bid,
               max_bid, ad_url, description, total_show,
               total_clicks, current_cost, active, username)
               VALUES (?,?,?,?,?,?,0,0,0,?,?)""",
            ('Top', 100, 1, 3, 'aaa.bbb.ccc', 'test2', True,
             make_secure_username('222')))

cur.execute("""INSERT INTO campaign (category, budget, min_bid,
               max_bid, ad_url, description, total_show,
               total_clicks, current_cost, active, username)
               VALUES (?,?,?,?,?,?,0,0,0,?,?)""",
            ('Bottom', 10, 1, 3, 'www.uuu.vvv', 'test3', True,
             make_secure_username('111')))

# add a customer
cur.execute("""INSERT INTO customer
               (username, password)
               VALUES (?,?)""",
            (make_secure_username('333'), make_secure_password('333')))


conn.commit()
conn.close()
