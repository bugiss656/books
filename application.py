import os, requests, json

from flask import Flask, render_template, session, url_for, redirect, request, logging, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps
from forms import RegistrationForm, ReviewForm

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Class for make a Goodreads API request
class GoodreadsRatings:

    def __init__(self, title):
        self.title = title

    url = 'https://www.goodreads.com/book/title.json'

    def makeRequest(self):
        res = requests.get(self.url, params = {"key": "####", "title": self.title})

        return res


# Homepage endpoint
@app.route('/')
def index():
    return render_template('index.html')



# Register endpoint
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)", {'username': username, 'email': email, 'password': password})
        db.commit()

        flash('You account has been successfully created.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)



# Login endpoint
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_provided = request.form['username']
        password_provided = request.form['password']

        if username_provided != '' and password_provided != '':
            query_select_user = db.execute("SELECT * FROM users WHERE username = :username", {'username': username_provided})
            db.commit()
            user_data = query_select_user.fetchone()

            if user_data:
                password = user_data['password']

                if password_provided == password:
                    session['logged_in'] = True
                    session['username'] = username_provided
                    session['userid'] = user_data['userid']
                    flash('You have been successfully loged in.', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Username or password incorrect, please try again.', 'danger')
            else:
                flash('Username or password incorrect, please try again.', 'danger')
        else:
            flash('All fields must be filled.', 'danger')

    return render_template('login.html')



# Decorator function for checking if user is logged in and preventing from manual access to specific routes
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap



# Snippet for adding a dynamic variable to static links
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)



# Logout endpoint
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logout from your account.', 'info')

    return redirect(url_for('login'))



# Search books endpoint
@app.route('/search', methods=['GET', 'POST'])
@is_logged_in
def search():
    if request.method == 'POST':
        search_keyword = request.form['search']

        if search_keyword != '':
            query_select_books = db.execute("SELECT bookid, isbn, title, author, year FROM books WHERE isbn LIKE '{0}%' OR title LIKE '{1}%' OR title LIKE '%{1}%' OR title LIKE '%{1}' OR author LIKE '{1}%' OR author LIKE '%{1}%' OR author LIKE '%{1}'".format(search_keyword, search_keyword.title()))
            db.commit()
            books_data = query_select_books.fetchall()

            if books_data:
                return render_template('search.html', books_data=books_data)
            else:
                flash('No results found, please try again.', 'info')
        else:
            flash('You have to fill the input field.', 'info')

    return render_template('search.html')



# Individual book endpoint
@app.route('/book/<id>/')
def book(id):
    query_select_book = db.execute("SELECT bookid, isbn, title, author, year FROM books WHERE bookid = :id", {'id': id})
    query_select_reviews = db.execute("SELECT username, rating, review FROM reviews INNER JOIN users ON users.userid = reviews.userid WHERE bookid = :id", {'id': id})
    db.commit()

    book_details = query_select_book.fetchone()
    reviews = query_select_reviews.fetchall()

    session['bookid'] = book_details.bookid

    goodreads_rating = GoodreadsRatings(book_details.title)
    goodreads_data = goodreads_rating.makeRequest()

    query_select_review = db.execute("SELECT review FROM reviews WHERE bookid = :bookid AND userid = :userid", {'bookid': session['bookid'], 'userid': session['userid']})
    db.commit()

    user_review = query_select_review.fetchone()

    return render_template('book.html', book_details=book_details, reviews=reviews, user_review=user_review)



# Add review endpoint
@app.route('/addreview', methods=['GET', 'POST'])
def addReview():
    form = ReviewForm(request.form)

    if request.method == 'POST' and form.validate():
        rating = form.rating.data
        review = form.review.data

        query_insert = db.execute("INSERT INTO reviews(rating, review, userid, bookid) VALUES(:rating, :review, :userid, :bookid)", {'rating': rating, 'review': review, 'userid': session['userid'], 'bookid': session['bookid']})
        db.commit()

        flash('Review successfully added.', 'success')

        return redirect(url_for('book', id=session['bookid']))

    return render_template('addReview.html', form=form)



# Edit review endpoint
@app.route('/editreview', methods=['GET', 'POST'])
def editReview():
    form = ReviewForm(request.form)

    if request.method == 'POST' and form.validate():
        rating = form.rating.data
        review = form.review.data

        query_update = db.execute("UPDATE reviews SET rating = :rating, review = :review WHERE bookid = :bookid AND userid = :userid", {'rating': rating, 'review': review, 'bookid': session['bookid'], 'userid': session['userid']})
        db.commit()

        flash('Review successfully updated.', 'success')

        return redirect(url_for('book', id=session['bookid']))

    return render_template('editReview.html', form=form)



# Delete review endpoint
@app.route('/deletereview')
def deleteReview():
    query_delete = db.execute("DELETE FROM reviews WHERE bookid = :bookid AND userid = :userid", {'bookid': session['bookid'], 'userid': session['userid']})
    db.commit()

    flash('You have deleted your review', 'info')

    return redirect(url_for('book', id=session['bookid']))



# API access endpoint
@app.route('/api/<isbn>')
def api(isbn):
    query = db.execute("SELECT title, author, year, isbn FROM books JOIN reviews ON reviews.bookid = books.bookid WHERE isbn = :isbn", {'isbn': isbn})
    query_reviews_sum = db.execute("SELECT COUNT(review) AS reviews_sum FROM reviews JOIN books ON books.bookid = reviews.bookid WHERE isbn = :isbn", {'isbn': isbn})
    query_rating_avg = db.execute("SELECT ROUND(AVG(rating), 2) AS rating_avg FROM reviews JOIN books ON books.bookid = reviews.bookid WHERE isbn = :isbn", {'isbn': isbn})
    db.commit()

    book_info = query.fetchone()
    book_reviews_sum = query_reviews_sum.fetchone()
    book_rating_avg = query_rating_avg.fetchone()

    if book_info and book_reviews_sum and book_rating_avg:
        response_object = {
            "title": book_info.title,
            "author": book_info.author,
            "year": book_info.year,
            "isbn": book_info.isbn,
            "review_count": book_reviews_sum.reviews_sum,
            "average_score": str(book_rating_avg.rating_avg)
        }

        response = json.dumps(response_object)

        return response

    else:
        return render_template('404.html')



if __name__ == '__main__':
    app.run(debug=True)
