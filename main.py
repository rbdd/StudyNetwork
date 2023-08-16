# imports
import re
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, Blueprint, g, abort
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from sqlalchemy import desc

#imports from the project
from models import db
import models
from forms import Sign_in, Sign_up, Post, Comment

#SQL query executer
def sqlite_conn(database, query, single=False):
    'connects to a database and returns data'
    conn = sqlite3.connect(database)
    cur = conn.cursor() 
    cur.execute(query) 
    results = cur.fetchone() if single else cur.fetchall() 
    conn.close() 
    return results 

app = Flask(__name__)
app.config.from_object(Config)
with app.app_context():
    db.init_app(app)

#routes#
@app.route('/', methods=['GET', 'POST'])
def home():
    'The homepage route'
    # gets all the posts in the database
    post = models.Post.query

    sort_option = request.args.get('sort')
    if sort_option == 'comments (most comment)':
        post = post.order_by(desc(models.Post.comments))
    elif sort_option == 'comments (least comment)':
        post = post.order_by(models.Post.comments)
    elif sort_option == 'most likes':
        post = post.order_by(desc(models.Post.likes))
    elif sort_option == 'least likes':
        post = post.order_by(models.Post.likes)
    elif sort_option == 'date (ascending)':
        post = post.order_by(models.Post.id)
    else:  # Default sorting: by date
        post = post.order_by(desc(models.Post.id))

    post = post.all()

    session['selectedOption'] = sort_option

    number_of_items = len(post)

    return render_template('home.html', posts=post, title='home', n=int(number_of_items))


@app.route('/comment/<int:id>', methods=['GET', 'POST'])
def comment(id):
    'Route for comment'
    form = Comment()
    post_info = db.session.query(models.Post).filter_by(id = id).first_or_404()
    user_info = db.session.query(models.User).filter_by(id = session['logged_in_user']).first()
    comments = db.session.query(models.Comment).filter_by(Post_id = id).all()
    notification_info = models.Notification()
    notification_info.user_id = post_info.user_id
    notification_info.sender = user_info.username
    notification_info.post_id = id

    # when no one is logged in, tells the user to sign up
    if g.logged_in_user == None:
        return redirect(url_for('signin'))

    elif request.method == 'GET':# display all the comments in the post

        if comments == None:
            return render_template('comment.html', form=form, post_info=post_info)

        else:
            return render_template('comment.html', form=form, comments=comments, post_info=post_info)

    else: #when someone trys to make a comment, make a comment and notify the owner of the post
        if form.validate_on_submit():
            if 'post' in request.form:
                comment_info = models.Comment()
                comment_info.Post_id = id
                comment_info.User_id = session['logged_in_user']
                comment_info.comment = form.comment.data
                db.session.add(comment_info)
                post_info.comments += 1
                if user_info.id != post_info.user_id:
                    notification_info.content = user_info.username + " replied to your question [" + post_info.title + "] : " + form.comment.data
                    db.session.add(notification_info)
            if 'like' in request.form:
                post_info.likes += 1
                if user_info.id != post_info.user_id:
                    notification_info.content = user_info.username + f" promoted your question [{post_info.title}]"
                    db.session.add(notification_info)
            db.session.commit()
            return redirect(url_for('comment',id=id))


@app.route('/post', methods=['GET', 'POST'])
def post():
    'Route for post. Allows the player to make new posts.'
    form = Post()

    # when no one is logged in, tells the user to sign up
    if g.logged_in_user == None:
        return redirect(url_for('signin'))

    # when user tries to make a post, lets the user to do so haha..     
    elif request.method == 'GET':
        return render_template('post.html', form=form, title='post')

    # when user triggers the submit button
    else:
        if form.validate_on_submit():
            post_info = models.Post()
            post_info.title = form.title.data
            post_info.discussion = form.discussion.data
            post_info.date = date.today().strftime('%d%m%Y')
            post_info.comments = 0
            post_info.likes = 0
            post_info.user_id = session['logged_in_user']            
            post_info = db.session.merge(post_info)

            for catego in form.category.data: 
                category = db.session.query(models.Category).filter_by(id = catego).first()
                post_info.categories_post.append(category)

            db.session.add(post_info)
            db.session.commit()
            return redirect(url_for('home'))

    return render_template('post.html', form=form, title='post')
        

@app.route('/notification', methods=['GET', 'POST'])
def notification():
    'Notification route. Displays all notifications that belong to the logged in user.'
    # when no one is logged in, tells the user to sign up
    if g.logged_in_user == None:
        return redirect(url_for('signin'))

    else: 
        #Show all the notification to the user 
        notifications = models.Notification.query.filter_by(user_id = session['logged_in_user']).order_by(desc(models.Notification.id)).all()
        return render_template('notification.html', notifications=notifications, title='notification')


@app.route('/mark_read/<int:id>/<int:pid>/<int:bid>', methods=['GET'])#bid is a short for boolean id
def mark_read(id, pid, bid): #pid is post id
    'A route that deletes the notifications which are read'
    notifications = models.Notification.query.filter_by(user_id = session['logged_in_user']).all()

    if bid == 1:
        noti_to_delete = models.Notification.query.filter_by(id = id).first_or_404()
        noti_to_delete = db.session.merge(noti_to_delete)
        db.session.delete(noti_to_delete)
        db.session.commit()
        return redirect(url_for('comment', id=pid))

    elif bid == 0:
        noti_to_delete = models.Notification.query.filter_by(user_id = session['logged_in_user']).all()     
        for x in range(len(noti_to_delete)):
            db.session.delete(db.session.merge(noti_to_delete[x]))
        db.session.commit()
        return redirect(url_for('notification'))

    else:
        abort(404)


@app.route('/profile/<int:id>')
def profile(id):
    'Profile route. If the user is signed in, it returns the profile page with user info. Else returns signup page'
    #Shows the basic information of a user with a certain id. 
    user_info = models.User.query.filter_by(id = id).first_or_404()
    post_info = models.Post.query.filter_by(user_id = id).order_by(desc(models.Post.id)).all()

    if g.logged_in_user:
        logged_in_user_info = models.User.query.filter_by(id = session['logged_in_user']).first_or_404()
        return render_template('profile.html', user=user_info, post=post_info, loginuser=logged_in_user_info)

    else:
        return render_template('profile.html', user=user_info, post=post_info)


@app.route('/delete_post/<int:id>')
def delete_post(id):
    'A route that allows the players to delete their post'
    post_to_delete = models.Post.query.filter_by(id = id).first_or_404()
    noti_to_delete = models.Notification.query.filter_by(post_id = id).all()
    post_to_delete = db.session.merge(post_to_delete)
    db.session.delete(post_to_delete)
    for x in range(len(noti_to_delete)):#These codes will delete the notifications which were associated to 
            db.session.delete(db.session.merge(noti_to_delete[x]))# the deleted post, 
    db.session.commit()
    return redirect(url_for('profile', id=session['logged_in_user']))


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    'Sign in route. Checks if the user information is correct and redirects to profile page.'    
    form = Sign_in()

    usern = models.User.query.filter_by(username = request.form.get('username_or_email')).first()
    usere = models.User.query.filter_by(email = request.form.get('username_or_email')).first()
    
    password = request.form.get('password')

    if request.method == 'GET': #If browser asked to see the page
        return render_template('signin.html', form=form, title='user')

    else:#When the user clicks the sign_in button
        if form.validate_on_submit():
            session.pop('logged_in_user', None)
            #Check if the username/password is matching
            if usern == None and usere == None:
                return render_template('signin.html', form=form, error = 'Typed username/email does not exist. Please sign up first. ')

            else:
                try:
                    passwith = check_password_hash(usern.password, password)                             
                except:
                    passwith = check_password_hash(usere.password, password)
                finally:                  
                    if not passwith:
                        return render_template('signin.html', form=form, error = 'Unable to signin. Please check your username/password again') 

            #redirects profile if it matches
            if usere == None:
                session['logged_in_user'] = usern.id
                return redirect(url_for('profile', id=session['logged_in_user']))

            else:
                session['logged_in_user'] = usere.id
                return redirect(url_for('profile', id=session['logged_in_user']))

        else:
            return render_template('signin.html', form=form, title='user', error = 'Unable to signin. Please check your username/password again')


@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    'Sign up route. Allows you to create a new account with the input information if possible.'
    form = Sign_up()
    if request.method == 'GET': #If browser asked to see the page
        return render_template('signup.html', form=form, title='sign_up')
    
    #When the user clicks the sign_up button
    else:
        if form.validate_on_submit():
            if models.User.query.filter_by(username = form.username.data).first() != None:
                return render_template('signup.html', form=form, error = 'username already in use')

            if models.User.query.filter_by(email = form.email.data).first() != None:
                return render_template('signup.html', form=form, error = 'email already in use')

            if len(request.form.get('password')) < 8:
                return render_template('signup.html', form=form, error='password must be atleast 8 letters')

            if form.password.data != form.re_password.data:
                return render_template('signup.html', form=form, error = 'your passwords do not match. Please try again')

            else:# if possible, create an account. 
                user_info = models.User(
                    username = form.username.data,
                    email = form.email.data,
                    #Hash the password for extra security
                    password = generate_password_hash(form.password.data, method='sha256')
                )
                db.session.add(user_info)
                db.session.commit()
                return redirect(url_for('signin'))     

        else:
            return render_template('signup.html', form=form, title='sign_up', error='The email is invalid')


@app.route('/logout')
def logout():
    'Route for logout.'
    session.pop('logged_in_user', None)
    return redirect(url_for('signin'))


@app.context_processor
def notification_processor():
    'used to pass on the number of notifications to the nav bar'
    if  g.logged_in_user:
        num_notification = models.Notification.query.filter_by(user_id = session['logged_in_user']).all()
        if len(num_notification) > 99:
            return dict(num_notification = '99..') #When the number of notification is too big, it just shows 99+.

        else:   
            return dict(num_notification = len(num_notification))

    else:
        return dict(num_notification = 'No one is logged in')


@app.before_request
def before_request():
    'Called before the request, checks if anybody is logged in.'
    g.logged_in_user = None
    if 'logged_in_user' in session:
        g.logged_in_user = session['logged_in_user']


@app.errorhandler(404)
def return_error(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)