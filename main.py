from crypt import methods
import json
from flask import Flask, render_template, request, send_file
import pandas as pd
import statistics
import numpy as np
from random import randint, random, choice
import string, json, os
from flask_mail import Mail, Message

from sqlalchemy import create_engine, insert
app = Flask(__name__)

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/fireEmail", methods=["POST"])
def generatemail():
    req = request.get_json()
    df = pd.read_csv('data/' + req['filename'])
    df[['Month','Day']] = df["Date"].str.split("/", 1, expand=True);
    df = df.astype({'Month':'int'})

    df['Type'] = np.where(df["Transaction"] > 0 , "Credit", "Debit")

    balance_month = df.groupby("Month")["Transaction"].count()
    balance = df["Transaction"].sum()
    average_credit =  df.groupby(["Month", "Type"])["Transaction"].mean().reset_index()
    #return average_credit.to_dict()
    sendEmail( render_template("summary.html", total_balance=round(balance, 2), balance_month=balance_month.to_dict(), average_credit=average_credit.to_html(index=False, classes=["table-email"]) ), req["email"])
    return df.to_dict();


@app.route("/generateCSV")
def generateRandomData():
    y = randint(1, 100)
    random_list = []
    for x in range(y):
        random_list.append([x, str(randint(1,12))+"/"+""+str(randint(1,28)), round(choice([-1,1])*random() *100, 2)])        
    engine = create_engine("mysql+mysqldb://admin:"+'cehxuk-paxqec-sowHo3'+"@database-1.ctwyx4gwfp3n.us-east-1.rds.amazonaws.com/stori")
    ls = pd.DataFrame(random_list, columns=["Id", "Date", "Transaction"])
    filename = get_random_string(30)+".csv"
    file = open("data/"+filename, "w")
    file.write(ls.to_csv(index=False))
    file.close()
    csv_id = 0
    with engine.connect() as connection: 
        id = connection.execute(f"INSERT INTO csv (filename, transactions) VALUES ('{filename}', {y})  ")
        csv_id = id.lastrowid
    ls["csv_id"] = csv_id
    
    ls.to_sql("Transactions",con=engine,index=False, if_exists="append" )

    response = {"Transactions": y,  "Filename": filename} 
    return json.dumps(response)

@app.route("/getCSVList")
def getCSVList():
    csvs = os.listdir("data")
    return json.dumps(csvs)

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(choice(letters) for i in range(length))
    return result_str


@app.route("/email")
def sendEmail(html, email):
    app.config['MAIL_SERVER']='smtp.hostinger.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'dev@dogker.xyz'
    app.config['MAIL_PASSWORD'] = 'cehxuk-paxqec-sowHo3'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)

    msg = Message('Stori Account Summary', sender = 'dev@dogker.xyz', recipients = [email])
    msg.body = "This is the email body"
    msg.html = html
    mail.send(msg) 
    return "Sent"

@app.route("/downloadCSV/<path:filename>")
def downloadCSV(filename): 
   return send_file("data/"+filename, mimetype="text/csv", as_attachment=True)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
