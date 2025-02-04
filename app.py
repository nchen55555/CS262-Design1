from flask import Flask, render_template
import sqlite3

# Configure application
app = Flask(__name__)

#connects to the camps database
db = sqlite3.connect("chat.db", check_same_thread = False)

#creates a table called messages under the chat database
db.execute("CREATE TABLE IF NOT EXISTS 'messages' ('message_id' INTEGER NOT NULL UNIQUE PRIMARY KEY, 'account_from_id' INTEGER NOT NULL UNIQUE, 'account_to_id' INTEGER NOT NULL UNIQUE, 'message_content' TEXT NOT NULL)")    
#creates a table called accounts under the chat database
db.execute("CREATE TABLE IF NOT EXISTS 'accounts' ('account_id' INTEGER NOT NULL UNIQUE PRIMARY KEY, 'username' TEXT NOT NULL, 'pass_hash' TEXT NOT NULL)")   

#home page 
@app.route("/")
def index():
    """Show homepage"""
    accounts = db.execute("SELECT * FROM accounts").fetchall()
    print(accounts)
    return render_template("index.html")

#blog page
@app.route("/messages")
def messages():
    """Show messages page"""
    messages = db.execute("SELECT message_id, message_content, account_from_id, account_to_id FROM messages").fetchall()
    return render_template("messages.html", messages = messages)



