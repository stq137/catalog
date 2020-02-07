#!/usr/bin/env python2
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, Users
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///categoriesmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Handle Google sign in."""
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
            connected.'), 200)
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
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = Users(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(Users).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    """Revoke a current user's token and reset their login session."""
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If the given token was invalid notice the user.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
def ShowAllCategoriesPublic():
    """
    ShowAllCategoriesPublic: function to retrieve all categories in DB
    Returns:
        HTML page with all categories in DB
    """
    all_categories = session.query(Categories).order_by(Categories.name)
    if 'username' not in login_session:
        return render_template(
            'all_categories_public.html', all_categories=all_categories)
    else:
        return render_template(
            'all_categories_loggedin.html', all_categories=all_categories)


@app.route('/catalog/<string:categories_name>/items/')
def ShowCategoryItemsPublic(categories_name):
    """
    ShowCategoryItemsPublic: function to retrieve all
    items in specific category in DB
    Args:
        categories_name (data type: string): category name
    Returns:
        HTML page with all items for categories_name in DB
    """
    category_name = session.query(Categories).filter_by(
        name=categories_name).one()
    items = session.query(Items).filter_by(
        category_id=category_name.id).all()
    if 'username' not in login_session:
        return render_template(
            'all_category_items_public.html',
            category_name=category_name, items=items)
    else:
        return render_template(
            'all_category_items_loggedin.html',
            category_name=category_name, items=items)


@app.route('/catalog/<string:categories_name>/<string:items_name>/')
def ShowItemDescription(categories_name, items_name):
    """
    ShowItemDescription: function retrieve item
    description for specific item in DB
    Args:
        categories_name(data type: string): category name
        items_name(data type: string): item name
    Returns:
        HTML page with items_name description
    """
    category_name = session.query(Categories).filter_by(
        name=categories_name).one()
    item = session.query(Items).filter_by(
        name=items_name, category_id=category_name.id).first()
    if 'username' not in login_session:
        return render_template(
            'item_description.html', category_name=category_name, item=item)
    else:
        return render_template(
            'item_description_loggedin.html',
            category_name=category_name, item=item)


@app.route('/addcategory/', methods=['GET', 'POST'])
def AddNewCategory():
    """Add new category to categories table"""
    if 'username' not in login_session:
        return redirect('/')
    if request.method == 'POST':
        newCategory = Categories(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New Category %s Successfully Created' % newCategory.name)
        return redirect(url_for('ShowAllCategoriesPublic'))
    else:
        return render_template('new_category.html')


@app.route('/loggedin/', methods=['GET', 'POST'])
def AddNewItem():
    """Add new item to items table"""
    if 'username' not in login_session:
        return redirect('/')
    all_categories = session.query(Categories).all()

    if request.method == 'POST':
        newItem = Items(
            name=request.form['name'], description=request.form['description'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('ShowAllCategoriesPublic'))
    else:
        return render_template('new_item.html', all_categories=all_categories)


@app.route(
    '/catalog/<string:categories_name>/<string:items_name>/edit/',
    methods=['GET', 'POST'])
def EditCategoryItem(categories_name, items_name):
    """
    EditCategoryItem: function to edit item
    for specific category in DB
    Args:
        categories_name(data type: string): category name
        items_name(data type: string): item name
    Returns:
        HTML page to edit items_name
    """
    if 'username' not in login_session:
        return redirect('/')
    category_name = session.query(Categories).filter_by(
        name=categories_name).one()
    item = session.query(Items).filter_by(
        name=items_name, category_id=category_name.id).one()
    if item.user_id != login_session['user_id']:
        return """<script>function myFunction()
        {alert('You are not the creator of this item,
        create your own item in order to edit.');}
        </script><body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        flash('Item %s Successfully Edited' % (item.name))
        return redirect(url_for('ShowAllCategoriesPublic'))
    else:
        return render_template(
            'edit_item.html', category_name=category_name, item=item)


@app.route(
    '/catalog/<string:categories_name>/<string:items_name>/delete/',
    methods=['GET', 'POST'])
def DeleteCategoryItem(categories_name, items_name):
    """
    DeleteCategoryItem: function to delete item
    for specific category in DB
    Args:
        categories_name(data type: string): category name
        items_name(data type: string): item name
    Returns:
        HTML page to delete items_name
    """
    if 'username' not in login_session:
        return redirect('/')
    category_name = session.query(Categories).filter_by(
        name=categories_name).one()
    item = session.query(Items).filter_by(
        name=items_name, category_id=category_name.id).first()
    if item.user_id != login_session['user_id']:
        return """<script>function myFunction()
        {alert('You are not the creator of this item,
        create your own item in order to delete.');}
        </script><body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item %s Successfully Deleted' % (item.name))
        return redirect(url_for('ShowAllCategoriesPublic'))
    else:
        return render_template(
            'delete_item.html', category_name=category_name, item=item)


@app.route('/catalog.json/')
def CategoriesJSON():
    """
    CategoriesJSON: function to give DB's data in json format
    Returns:
        HTML page in json format for selected DB's data
    """
    all_categories = session.query(Categories).order_by(Categories.id)
    items = session.query(Items).order_by(Items.category_id)
    return jsonify(
        Category=[i.serialize for i in all_categories],
        Items=[i.serialize for i in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000, threaded=False)
