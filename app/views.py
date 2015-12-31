#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, EditForm, PostForm, SearchForm
from models import User, Post
from datetime import datetime
from config import POSTS_PER_PAGE, UPLOAD_FOLDER, UPLOAD_LOCAL_FOLDER, HEAD_FOLDER, HEAD_LOCAL_FOLDER
import os
import uuid
from werkzeug.utils import secure_filename
import time


@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page = 1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body = form.post.data, timestamp = datetime.utcnow(), author = g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))

    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template("index.html",
        title = 'Home',
        form = form,
        posts = posts)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        user = User.query.filter_by(nickname = form.username.data).first()
        
        # make the user follow him/herself
        u = user.follow(user)
        if u is not None:
            db.session.add(u)
            db.session.commit()        

        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user, remember = remember_me)
        return redirect(request.args.get('next') or url_for('index'))

    return render_template('login.html',
        title = 'Sign In',
        form = form,
    )
    

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()
    
@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page = 1):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False) 
    return render_template('user.html', 
        user = user,
        posts = posts
    )

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        f = request.files['head']
        if f != None and f.filename != None and f.filename != "":
            fname = str(int(time.time())) + f.filename
            f.save(os.path.join(HEAD_FOLDER, fname))
            g.user.avatar = os.path.join(HEAD_LOCAL_FOLDER, fname)
        g.user.nickname = form.username.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes hava been saved')
        return redirect(url_for('edit'))
    else:
        form.username.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form = form)

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname = nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    return redirect(url_for('user', nickname = nickname))

@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname = nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('user', nickname = nickname))


@app.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query = g.search_form.search.data))

from config import MAX_SEARCH_RESULTS

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    # FIXME 中文无法查询
    posts = Post.query.filter(Post.title.ilike('%'+ query +'%')).order_by(-Post.timestamp).limit(MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html',
        query = query,
        posts = posts)

@app.route('/ck_edit', methods = ['GET', 'POST'])
@login_required
def ck_edit():
    return render_template('ck_edit.html')

@app.route('/img_upload', methods = ['POST'])
@login_required
def img_upload():
    callback = request.args['CKEditorFuncNum']
    f = request.files['upload']
    fname = str(uuid.uuid1()) + '.' +  str(f.filename.split('.')[1])
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    f.save(os.path.join(UPLOAD_FOLDER, fname))
    return_data = ""
    return_data += "<script type=\"text/javascript\">"
    return_data += "window.parent.CKEDITOR.tools.callFunction(" + callback + ",'" + '/' + UPLOAD_LOCAL_FOLDER + '/' + fname + "','')"
    return_data += "</script>"
    print return_data
    return return_data

@app.route('/post_blog', methods = ['POST'])
@login_required
def post_blog():
    title = request.form.get('title', None)
    body = request.form.get('content', None)
    if body is not None and title is not None:
        post = Post(body = body, title = title, timestamp = datetime.utcnow(), author = g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/show_blog/<int:id>', methods = ['GET'])
@login_required
def show_blog(id):
    post = Post.query.get(id)
    return render_template('show_blog.html', post = post)
