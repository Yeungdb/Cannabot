#!/usr/bin/python

import os
import json
import requests
from urlparse import urlparse, urljoin
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify 
from flask.ext.login import LoginManager
app = Flask(__name__)
app.secret_key = os.environ['CANNAKEY']
login_manager = LoginManager()
login_manager.init_app(app)

import DBInterface as DBI
db = DBI.DatabaseAccess()

example = open('templates/example_products.json').read() 

def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print(db.isLoggedIn)
        if not db.isLoggedIn:
            return redirect(url_for("Login"))
        return f(*args, **kwargs)
    return wrapper

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.route("/")
def Index():
    return render_template('index.html')

@app.route("/Patient")
def PatientForm():
    return render_template('RegisterPatientForm.html')

@app.route("/Dispensary")
def DispensaryForm():
    return render_template('RegisterDispensaryForm.html')

@app.route("/PatientResult", methods=['POST'])
def RegisterPatient():
    PatientInfo = request.form
    db.AddUserInfo(PatientInfo['patientname'], PatientInfo['tel'], PatientInfo['dispensaryname'], PatientInfo['addr'])
    #Do a pop up say something like, thank you for the registration, you will need to contact dispensary to approve of your account.
    return redirect(url_for("Index"))

@app.route("/DispResult", methods=['POST'])
def RegisterDisp():
    DispInfo = request.form
    print(DispInfo)
    db.AddDispensary(DispInfo['name'], DispInfo['contactname'], DispInfo['email'], int(DispInfo['tel']), DispInfo['addr'], DispInfo['LoginName'], DispInfo['PD'])
    #Do a pop up and say thank you for signing up.
    return redirect(url_for("Index"))

@app.route('/DispensarySignin', methods=['GET', 'POST'])
def Login():
    return render_template('DispensarySignin.html')

@app.route('/AuthDispensarySignin', methods=['GET', 'POST'])
def AuthLogin():
    DispInfo = request.form
    session['username'] = DispInfo['LoginName']
    if DispInfo['LoginName'] == "" or DispInfo['PD'] == "":
        return redirect(url_for('Login'))
    db.Authenticate(DispInfo['LoginName'], DispInfo['PD'])
    if db.isLoggedIn:
        return redirect(url_for('Approval'))
    else:
        return redirect(url_for('Login'))

@app.route('/OnPressApprove', methods=['GET', 'POST'])
def OnPressApprove():
    phoneNumber = int(json.dumps(request.get_data())[1:-1])
    db.InitUser(phoneNumber)
    DispId, DispName = db.GetDispensaryInfoFromUserPhone(phoneNumber)[0]
    jsonReturn = {}
    jsonReturn['phonenumber']=phoneNumber
    jsonReturn['dispensaryid']=DispId
    jsonReturn['dispensaryname']=DispName
    jsonReturn = json.dumps(jsonReturn)
    print jsonReturn
    headers = {
            'content-type': 'application/json'
            }
    data = jsonReturn
    resp = requests.post('http://ca31907e.ngrok.io/sendUser', headers=headers, data=data)
    print resp.text, resp.status_code
    return (resp.text, resp.status_code, resp.headers.items())
@app.route('/ApproveUsers', methods=['GET', 'POST'])
@authenticate
def Approval():
    data = db.GetUnactivatedUser(session['username'])
    return render_template('Approval.html', result=data)


@app.route('/Logout')
@authenticate
def Logout():
    session.pop('username', None)
    db.isLoggedIn = 0
    return redirect(url_for('Index'))

@app.route('/GetProduct')
def GetProduct():
    return example 


if __name__ == "__main__":
    app.run()
