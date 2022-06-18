from distutils.log import Log
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/register', methods=["GET", "POST"])
def register_user():
    if 'user_id' in session: 
        username = session['user_id']
        return redirect(f'/users/{username}')

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.username

        flash('Welcome! Successfully created your account')
        return redirect(f'/users/{new_user.username}')

    return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login_user():
    if 'user_id' in session: 
        username = session['user_id']
        return redirect(f'/users/{username}')

    form = LoginForm()

    if form.validate_on_submit(): 
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user: 
            flash(f"Welcome Back, {user.first_name}!")
            session['user_id'] = user.username
            return redirect(f'/users/{user.username}')
        else: 
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

@app.route('/logout', methods=['POST'])
def logout_user(): 
    session.pop('user_id')
    flash("Succefully Logged You Out!")
    return redirect('/login')


@app.route('/users/<username>')
def users_page(username):
    if 'user_id' not in session: 
        flash('Please login first')
        return redirect('/login')

    user = User.query.get_or_404(username)
    form = FeedbackForm()
    
    return render_template('user_page.html', user=user, form=form)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'user_id' not in session: 
        flash('Please login first')
        return redirect('/login')
    user = User.query.filter_by(username=username).first()
    if user.username == session['user_id']:
        db.session.delete(user)
        db.session.commit()
        session.pop('user_id')
        return redirect('/')
    else:
        return redirect(f'/users/{user.username}')

@app.route('/users/<username>/feedback/add', methods=["POST"])
def add_feedback(username):
    if 'user_id' not in session: 
        flash('Please login first')
        return redirect('/login')

    form = FeedbackForm()

    user = User.query.filter_by(username=username).first()
    if user.username == session['user_id']: 
        title = form.title.data
        content = form.content.data
        adding_user = user.username
        new_feedback = Feedback(title=title, content=content, username=adding_user)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{user.username}')
    else: 
        return redirect(f'/users/{user.username}')

@app.route('/feedback/<int:id>/update', methods=["GET", "POST"])
def update_feedback(id):
    if 'user_id' not in session: 
        flash('Please login first')
        return redirect('/login')

    feedback = Feedback.query.get_or_404(id)
    if feedback.user.username == session['user_id']:
        form = FeedbackForm(obj=feedback)

        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data

            db.session.commit()
            return redirect(f'/users/{feedback.user.username}')


        return render_template('update_feedback.html', feedback=feedback, form=form)
    else: 
        return redirect('/')


@app.route('/feedback/<int:id>/delete')
def delete_feedback(id):
    if 'user_id' not in session: 
        flash('Please login first')
        return redirect('/login')

    feedback = Feedback.query.get_or_404(id)
    if feedback.user.username == session['user_id']:
        db.session.delete(feedback)
        db.session.commit()

        return redirect(f'/users/{feedback.user.username}')
    else: 
        return redirect('/')