from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Data_Setup import Base, SwitchCompanyName, SwitchName, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///switches.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Switches Store"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tbs_cat = session.query(SwitchCompanyName).all()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tbs_cat = session.query(SwitchCompanyName).all()
    tbes = session.query(SwitchName).all()
    return render_template('login.html',
                           STATE=state, tbs_cat=tbs_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # tbs_cat=tbs_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    User1 = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(User1)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#####
# Home


@app.route('/')
@app.route('/home')
def home():
    tbs_cat = session.query(SwitchCompanyName).all()
    return render_template('myhome.html', tbs_cat=tbs_cat)

#####
# Switch Category for admins


@app.route('/SwitchStore')
def SwitchStore():
    try:
        if login_session['username']:
            name = login_session['username']
            tbs_cat = session.query(SwitchCompanyName).all()
            tbs = session.query(SwitchCompanyName).all()
            tbes = session.query(SwitchName).all()
            return render_template('myhome.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))

######
# Showing switches based on switch category


@app.route('/SwitchStore/<int:tbid>/AllCompanys')
def showSwitches(tbid):
    tbs_cat = session.query(SwitchCompanyName).all()
    tbs = session.query(SwitchCompanyName).filter_by(id=tbid).one()
    tbes = session.query(SwitchName).filter_by(switchcompanynameid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showSwitches.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showSwitches.html',
                               tbs_cat=tbs_cat, tbs=tbs, tbes=tbes)

#####
# Add New Switch


@app.route('/SwitchStore/addSwitchCompany', methods=['POST', 'GET'])
def addSwitchCompany():
    if "username" not in login_session:
        flash("Please login first")
        return redirect(url_for("showLogin"))
    if request.method == 'POST':
        company = SwitchCompanyName(name=request.form['name'],
                                    user_id=login_session['user_id'])
        session.add(company)
        session.commit()
        return redirect(url_for('SwitchStore'))
    else:
        return render_template('addSwitchCompany.html', tbs_cat=tbs_cat)

########
# Edit Switch Category


@app.route('/SwitchStore/<int:tbid>/edit', methods=['POST', 'GET'])
def editSwitchCategory(tbid):
    editedSwitch = session.query(SwitchCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(editedSwitch.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Switch Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('SwitchStore'))
    if request.method == "POST":
        if request.form['name']:
            editedSwitch.name = request.form['name']
        session.add(editedSwitch)
        session.commit()
        flash("Switch Category Edited Successfully")
        return redirect(url_for('SwitchStore'))
    else:
        # tbs_cat is global variable we can them in entire application
        return render_template('editSwitchCategory.html',
                               tb=editedSwitch, tbs_cat=tbs_cat)

######
# Delete Switch Category


@app.route('/SwitchStore/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteSwitchCategory(tbid):
    tb = session.query(SwitchCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Switch Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('SwitchStore'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("Switch Category Deleted Successfully")
        return redirect(url_for('SwitchStore'))
    else:
        return render_template('deleteSwitchCategory.html', tb=tb,
                               tbs_cat=tbs_cat)

######
# Add New Switch Name Details


@app.route('/SwitchStore/addCompany/addSwitchDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addSwitchDetails(tbname):
    tbs = session.query(SwitchCompanyName).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of switch
    creator = getUserInfo(tbs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showSwitches', tbid=tbs.id))
    if request.method == 'POST':
        name = request.form['name']
        color = request.form['color']
        price = request.form['price']
        switchtype = request.form['switchtype']
        switchdetails = SwitchName(name=name,
                                   color=color,
                                   price=price,
                                   switchtype=switchtype,
                                   switchcompanynameid=tbs.id,
                                   user_id=login_session['user_id'])
        session.add(switchdetails)
        session.commit()
        return redirect(url_for('showSwitches', tbid=tbs.id))
    else:
        return render_template('addSwitchDetails.html',
                               tbname=tbs.name, tbs_cat=tbs_cat)

######
# Edit Switch details


@app.route('/SwitchStore/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editSwitch(tbid, tbename):
    tb = session.query(SwitchCompanyName).filter_by(id=tbid).one()
    switchdetails = session.query(SwitchName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of switch
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showSwitches', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        switchdetails.name = request.form['name']
        switchdetails.color = request.form['color']
        switchdetails.price = request.form['price']
        switchdetails.switchtype = request.form['switchtype']
        session.add(switchdetails)
        session.commit()
        flash("Switch Edited Successfully")
        return redirect(url_for('showSwitches', tbid=tbid))
    else:
        return render_template('editSwitch.html',
                               tbid=tbid, switchdetails=switchdetails,
                               tbs_cat=tbs_cat)

#####
# Delete Switch Edit


@app.route('/SwitchStore/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteSwitch(tbid, tbename):
    tb = session.query(SwitchCompanyName).filter_by(id=tbid).one()
    switchdetails = session.query(SwitchName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of switch
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showSwitches', tbid=tb.id))
    if request.method == "POST":
        session.delete(switchdetails)
        session.commit()
        flash("Deleted Switch Successfully")
        return redirect(url_for('showSwitches', tbid=tbid))
    else:
        return render_template('deleteSwitch.html',
                               tbid=tbid, switchdetails=switchdetails,
                               tbs_cat=tbs_cat)

####
# Logout from current user


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected....'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type':
                           'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps
                                 ('Successfully disconnected user..'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('home'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#####
# Json


@app.route('/SwitchStore/JSON')
def allSwitchesJSON():
    switchcategories = session.query(SwitchCompanyName).all()
    category_dict = [c.serialize for c in switchcategories]
    for c in range(len(category_dict)):
        switches = [i.serialize for i in session.query(
                 SwitchName).filter_by(switchcompanynameid=category_dict[c]
                                       ["id"]).all()]
        if switches:
            category_dict[c]["switch"] = switches
    return jsonify(SwitchCompanyName=category_dict)

####


@app.route('/switchStore/switchCategories/JSON')
def categoriesJSON():
    switches = session.query(SwitchCompanyName).all()
    return jsonify(switchCategories=[c.serialize for c in switches])

####


@app.route('/switchStore/switches/JSON')
def itemsJSON():
    items = session.query(SwitchName).all()
    return jsonify(switches=[i.serialize for i in items])

####


@app.route('/switchStore/<path:switch_name>/switches/JSON')
def categoryItemsJSON(switch_name):
    switchCategory = session.query(SwitchCompanyName).filter_by(
        name=switch_name).one()
    switches = session.query(SwitchName).filter_by(
        switchcompanyname=switchCategory).all()
    return jsonify(switchEdtion=[i.serialize for i in switches])

#####


@app.route('/switchStore/<path:switch_name>/<path:edition_name>/JSON')
def ItemJSON(switch_name, edition_name):
    switchCategory = session.query(SwitchCompanyName)\
                     .filter_by(name=switch_name).one()
    switchEdition = session.query(SwitchName).filter_by(
           name=edition_name, switchcompanyname=switchCategory).one()
    return jsonify(switchEdition=[switchEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
