from flask import Flask, request, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import pickle
import requests
import hashlib

app = Flask(__name__)

movies = pickle.load(open('model/movies_list.pkl', 'rb'))
similarity = pickle.load(open('model/similarity.pkl', 'rb'))

app.secret_key = 'xyzsdfg'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'user_authentication'

mysql = MySQL(app)

def fetch_select_poster(id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    # print(full_path)
    return full_path

def fetch_select_overview(id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    movie_overview = data['overview']
    return movie_overview

def fetch_select_rating(id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    movie_rating = data['vote_average']
    return movie_rating

def fetch_select_genres(id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    movie_genres = data['genres']
    return movie_genres

def fetch_select_cast(id):
    url = "https://api.themoviedb.org/3/movie/{}/credits?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    movie_cast = data['cast'][:25]
    return movie_cast

def fetch_select_crew(id):
    url = "https://api.themoviedb.org/3/movie/{}/credits?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(id)
    data = requests.get(url)
    data = data.json()
    movie_crew = data['crew'][:25]
    return movie_crew

def movie_select_id(movie_name):
     id = movies[movies['title'] == movie_name].index[0]
     movie_select_id = movies.iloc[id].movie_id
     movie_select_poster = []
     movie_select_overview = []
     movie_select_rating = []
     movie_select_genres = []
     movie_select_cast = []
     movie_select_crew = []
     movie_select_poster.append(fetch_select_poster(movie_select_id))
    #  print(movie_select_poster)
     overview_select = fetch_select_overview(movie_select_id)
     movie_select_overview.append(overview_select)
    #  print(overview_select)
     rating_select = fetch_select_rating(movie_select_id)
     movie_select_rating.append(rating_select)
    #  print(rating_select)
     genres_select = fetch_select_genres(movie_select_id)
     genres_list = [d['name'] for d in genres_select]
     genres = ", ".join(genres_list) 
     movie_select_genres.append(genres)
    #  print(genres)
     cast_select = fetch_select_cast(movie_select_id)
     cast_list = [d['name'] for d in cast_select]
     cast = ", ".join(cast_list) 
     movie_select_cast.append(cast)
    #  print(cast)
     crew_select = fetch_select_crew(movie_select_id)
     crew_list = [d['name'] for d in crew_select]
     crew = ", ".join(crew_list) 
     movie_select_crew.append(crew)
    #  print(crew)
     return movie_select_poster, movie_select_overview, movie_select_rating, movie_select_genres, movie_select_cast, movie_select_crew

def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=523145d496ac570a67c08ee1d852dea8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def  recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse = True, key = lambda x: x[1])
    recommended_movies_name = []
    recommended_movies_poster = []
    recommended_movies_overview = []
    for i in distances[1:9]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies_poster.append(fetch_poster(movie_id))
        recommended_movies_name.append(movies.iloc[i[0]].title)
        overview_list = movies.iloc[i[0]].overview
        overview = " ".join(overview_list)
        recommended_movies_overview.append(overview)
    return recommended_movies_name, recommended_movies_poster, recommended_movies_overview

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['name']
        password = request.form['password']
        email = request.form['email']
        hashed_password = hashlib.sha256(password.encode()).hexdigest() # Hash the password using SHA-256 algorithm
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address !'
        elif not username or not password or not email:
            message = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (username, email, hashed_password,))
            mysql.connection.commit()
            message = 'You have successfully registered !'
    elif request.method == 'POST':
        message = 'Please fill out the form !'
    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest() # Hash the password using SHA-256 algorithm
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, hashed_password,))
        user = cursor.fetchone()
        if user:
            session['logged_in'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            return redirect(url_for("home"))
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('userid', None)
    session.pop('name', None)
    session.pop('email', None)
    return redirect(url_for("home"))

@app.route('/recommendation', methods = ['GET', 'POST'])
def recommendation():
    # print(movies)
      movie_list = movies['title'].values
      status = False
      if request.method == "POST":
        try:
            if request.form:
                movie_name = request.form['movies']
                # movie_select_poster = movie_select_id(movie_name)
                # print(movie_select_id)
                # print(movie_name)
                movie_select_poster, movie_select_overview, movie_select_rating, movie_select_genres, movie_select_cast, movie_select_crew = movie_select_id(movie_name)
                recommended_movies_name,  recommended_movies_poster, recommended_movies_overview = recommend(movie_name)
                # print(recommended_movies_name)
                # print(recommended_movies_poster)

                status = True
                
                return render_template("recommendation.html", movie_list = movie_list, movie_name = movie_name, movie_select_poster = movie_select_poster, movie_select_overview = movie_select_overview, recommended_movies_name = recommended_movies_name, poster = recommended_movies_poster,  recommended_movies_overview =  recommended_movies_overview,
                movie_select_rating = movie_select_rating, movie_select_genres = movie_select_genres, movie_select_cast = movie_select_cast, movie_select_crew = movie_select_crew, status = status)
                


        except Exception as e:
            error = {'error': e}
            return render_template("recommendation.html", movie_list = movie_list, status = status)

      else:
        return render_template("recommendation.html", movie_list = movie_list, status = status)
                

if __name__ == '__main__':
    app.debug = True
    app.run()