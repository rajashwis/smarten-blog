import mysql.connector
blog_data = mysql.connector.connect(host = "localhost", password = "Blues22#", user = "root", database = "smarten_blog")

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.jinja_env.filters['zip'] = zip
mycursor = blog_data.cursor(prepared = True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Blues22#@localhost/smarten_blog'
app.config['SECRET_KEY'] = "this is whatever"

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_filename(filename):
    return '.' in filename and filename.rsplit(".", 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


class Users(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), nullable = False)
    username = db.Column(db.String(20), nullable = False, unique = True)
    password = db.Column(db.String(128), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)

#Flask Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

@app.route('/')
@login_required
def index():
    """
    The 'homepage' of this blog, essentially. Displays all the articles that are stored in the blog.
    """

    mycursor = blog_data.cursor()
    mycursor.close()
    mycursor = blog_data.cursor()
    
    mycursor.execute('SELECT * FROM article')
    article_details = mycursor.fetchall()
    
    author_names = []
    author_ids = []

    for article in article_details:
        mycursor.execute(f'SELECT name, id FROM users WHERE id = {article[-1]}')
        author_details = mycursor.fetchall()
        author_names.append(author_details[0][0])
        author_ids.append(author_details[0][1])

    return render_template("posts.html", article_details = article_details, author_name = author_names)

#login page
@app.route('/login', methods = ['GET', 'POST'])
def login():
    """
    Helps users log in and access the blog if their data has been stored in the database.
    """

    if current_user.is_authenticated:
        flash("You're already logged in!", "warning")
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            username = request.form["username"]
            password = request.form["password"]
            print(password)

            if username and password:

                user = Users.query.filter_by(username = username).first()
                print(user.password)

                if user:

                    print("hello!")
                    if bcrypt.check_password_hash(user.password, password):
                        login_user(user, remember=True)
                        flash("You are now logged in!", "success")
                        return redirect(url_for('index'))
                    else:
                        flash("Wrong Password!", "danger")
                        
                else:
                    flash("Invalid Username!", "danger")
                
                return render_template("login.html") 

            else:
                flash("Please fill in all categories!", "danger")
                return render_template("login.html")

        else:
            return render_template("login.html")


@app.route('/register', methods = ['POST', 'GET'])
def register():

    """
    Helps user create a new account in our blog.
    """

    if current_user.is_authenticated:
        flash("Cannot register a new user when you're logged in!", "warning")
        return redirect(url_for('index'))

    else:
        if request.method == 'POST':
            email = request.form["email"]
            name = request.form["name"]
            username = request.form["username"]
            password = request.form["password"]
            password_duplicate = request.form["password_duplicate"]

            if email and username and password and password_duplicate:
                email_exists = Users.query.filter_by(email = email).first()
                username_exists = Users.query.filter_by(username = username).first()
                if email_exists:
                    flash("Email already in use!", "danger")
                elif username_exists:
                    flash("Username already in use!", "danger")
                elif password != password_duplicate:
                    flash("Passwords don't match!", "warning")
                else:
                    if len(password) >= 8  and len(password) <= 16:
                        upper = lower = digit = special = False
                        for password_ in password:
                            if password_.isupper():
                                upper = True
                            if password_.islower():
                                lower = True
                            if password_.isdigit():
                                digit = True 
                            if password_ in ["!","#","$","%","&","^","@","*"]:
                                special = True

                        if upper == True and lower == True and digit == True and special == True:
                            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
                            mycursor.execute(f'INSERT INTO users (username, name, email, password) VALUES ("{username}", "{name}", "{email}", "{hashed}")')
                            blog_data.commit()
                            flash("Your account was successfully created. Please log in with your new credentials!", "info")
                            return redirect(url_for('login'))

                        else:
                            requirements = '''
                            Invalid Password!! Make sure your password follows all these requirements:<br/><br/>
                            1. At least one uppercase letter<br/>
                            2. At lease one lowercase letter<br/>
                            3. At least one numeric value<br/>
                            4. At least one special character (!,#,$,%,^,&,*,@)
                            '''
                            flash(requirements, "warning")

                    else:
                        flash("Password length invalid! Password should be between 8-16 characters!", "warning")


                return redirect(url_for('register'))

            else:
                flash("Please fill all categories!", "danger")
                return redirect(url_for('register'))
        else:
            return render_template("registration.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out!", "success")
    return(redirect(url_for('login')))

with app.app_context():
    db.create_all()

@app.route('/posts/<post_id>')
@login_required
def posts_individual(post_id):
    
    mycursor.execute(f'SELECT * FROM article WHERE article_id = {post_id}')
    article_details = mycursor.fetchall()
    
    paragraphs = article_details[0][2].split("\r")

    mycursor.execute(f'SELECT name FROM users WHERE id = (SELECT author_no FROM article WHERE article_id = {post_id})')
    author_name = mycursor.fetchall()
    author_name = author_name[0][0]
    
    join_sql = '''
    SELECT t.tag_name, t.tag_id
    FROM tags t JOIN post_tags pt ON
        t.tag_id = pt.tag_no JOIN article a ON
            a.article_id = pt.article_no
    WHERE a.title = "{}"
    '''.format(article_details[0][1])
    
    mycursor.execute(join_sql)
    tag_details = mycursor.fetchall()
    
    print(tag_details)
    tag_names = []
    tag_ids = []
    
    for tag in tag_details:
        tag_names.append(tag[0])
        tag_ids.append(tag[1])
    
    #tag_list = ", ".join(tag_list)
    
    len_tags = (len(tag_names) - 1)
    return render_template("posts_individual.html", post = article_details, author_name = author_name, tag_names = tag_names, tag_ids = tag_ids, len_tags = len_tags, paragraphs = paragraphs)

@app.route('/tags/<tag_id>')
@login_required
def posts_with_tag(tag_id):

    mycursor.execute(f'SELECT * FROM article WHERE article_id IN (SELECT article_no FROM post_tags WHERE tag_no = {tag_id})')
    article_details = mycursor.fetchall()

    author_names = []

    for article in article_details:
        mycursor.execute(f'SELECT name FROM users WHERE id = {article[-1]}')
        author_name_results = mycursor.fetchall()
        author_names.append(author_name_results[0][0])

    mycursor.execute(f'SELECT tag_name FROM tags WHERE tag_id = {tag_id}')
    tag_name = mycursor.fetchall()
    tag_name = tag_name[0][0]


    return render_template("posts_with_tag.html", posts = article_details, author_names = author_names, tag_name = tag_name)


@app.route('/author/<author_id>')
@login_required
def posts_by_author(author_id):

    mycursor.execute(f'SELECT * FROM article WHERE author_no = {author_id}')
    article_details = mycursor.fetchall()

    author_names = []

    for article in article_details:
        mycursor.execute(f'SELECT name FROM users WHERE id = {article[-1]}')
        author_name_results = mycursor.fetchall()
        author_names.append(author_name_results[0][0])

    mycursor.execute(f'SELECT name FROM users WHERE id = {author_id}')
    author_name = mycursor.fetchall()
    author_name = author_name[0][0]

    return render_template("posts_by_author.html", article_details = article_details, author_names = author_names, author_name = author_name)

@app.route('/article-create', methods = ['POST','GET'])
@login_required
def article_create():
    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        content = request.form['content']
        image_file = request.files['image']
        tags = request.form['tags']
        
        author_id = current_user.id 
       
        #bringing out tag's id  
    
        mycursor.execute('SELECT * FROM tags')
        tag_details = mycursor.fetchall()
        
        tags_split = tags.split(", ")
        tag_names = []
        
        for tag in range(len(tag_details)):
            tag_names.append(tag_details[tag][1])
        
        tag_ids = []
        
        for tag in tags_split:
            if tag not in tag_names:
                mycursor.execute(f'INSERT INTO tags (tag_name) VALUES ("{tag}")')
            mycursor.execute(f'SELECT tag_id FROM tags WHERE tag_name = "{tag}"')
            tag_ids.append(mycursor.fetchall()[0][0])
        
        if image_file and allowed_filename(image_file.filename):
            filename = image_file.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_path = image_path[7:]
            image_path = image_path.replace("\\","/")

        mycursor.execute(f'INSERT INTO article (title, summary, content, image_path, author_no) VALUES ("{title}","{summary}", "{content}","{image_path}", "{author_id}")')
        mycursor.execute(f'SELECT LAST_INSERT_ID()')
        article_id = mycursor.fetchall()[0][0]
        
        for tag_id in tag_ids:
            mycursor.execute(f'INSERT INTO post_tags VALUES ({tag_id}, {article_id})')

        blog_data.commit()
        flash("Article Created!", "success")
        
        return redirect(url_for('posts_individual', post_id = article_id))

    else:
        return render_template("article_create.html")

    
@app.route('/article-update/<post_id>', methods = ['POST', 'GET'])
@login_required
def edit_article(post_id):

    mycursor.execute(f'SELECT id FROM users WHERE id = (SELECT author_no FROM article WHERE article_id = {post_id})')
    author_id = mycursor.fetchall()
    author_id = author_id[0][0]

    if author_id == current_user.id:
    
        if request.method == 'POST':

            title = request.form['title']
            summary = request.form['summary']
            content = request.form['content']
            image_file = request.files['image']
            tags = request.form['tags']
        
            #bringing out tag's id  
        
            mycursor.execute('SELECT * FROM tags')
            tag_details = mycursor.fetchall()
            
            tags_split = tags.split(", ")
            tag_names = []
            
            for name in range(len(tag_details)):
                tag_names.append(tag_details[name][1])
            
            tag_ids = []
            
            for tag in tags_split:
                if tag not in tag_names:
                    mycursor.execute(f'INSERT INTO tags (tag_name) VALUES ("{tag}")')
                mycursor.execute(f'SELECT tag_id FROM tags WHERE tag_name = "{tag}"')
                tag_ids.append(mycursor.fetchall()[0][0])

            for tag_id in tag_ids:
                try:
                    mycursor.execute(f'INSERT INTO post_tags VALUES ({tag_id}, {post_id})')
                except:
                    continue
            
            author_id = current_user.id

            if image_file and allowed_filename(image_file.filename):
                filename = image_file.filename
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                image_path = image_path[7:]
                image_path = image_path.replace("\\","/")
                print("image_path: ", image_path)
            else:
                mycursor.execute(f'SELECT * FROM article WHERE article_id = {post_id}')
                result = mycursor.fetchall()

                print(result)

                image_path = result[0][5]
                print("image_path: ", image_path)


            sql_query = '''
            UPDATE article 
            SET title = "{}", summary = "{}", content = "{}", image_path = "{}", author_no = "{}" 
            WHERE article_id = {}
            '''.format(title, summary, content, image_path, author_id, post_id)

            mycursor.execute(sql_query)

            blog_data.commit()

            flash("Article Updated!", "success")
                
            
            return redirect(url_for('posts_individual', post_id = post_id))

        else:

            
            mycursor.execute(f'SELECT * FROM article WHERE article_id = {post_id}')
            article_details = mycursor.fetchall()
            
            author_name = current_user.name
            
            join_sql = '''
            SELECT t.tag_name
            FROM tags t JOIN post_tags pt ON
                t.tag_id = pt.tag_no JOIN article a ON
                    a.article_id = pt.article_no
            WHERE a.title = "{}"
            '''.format(article_details[0][1])

            mycursor.execute(join_sql)
            tag_details = mycursor.fetchall()

            tag_names = []

            for tag in tag_details:
                tag_names.append(tag[0])
            
            tags = ', '.join(tag_names)
            
            title = article_details[0][1]
            summary = article_details[0][3]
            content = article_details[0][2]
            image_path = article_details[0][5]
            
            return render_template("article_update.html", title = title, content = content, summary = summary, image_path = image_path, tags = tags, author = author_name)
    
    else:
        flash("You aren't authorised!!", "danger")
        return redirect(url_for('index'))
        

@app.route('/delete-article/<post_id>', methods =['POST', 'GET'])
@login_required
def delete_article(post_id):

    mycursor.execute(f'SELECT id FROM users WHERE id = (SELECT author_no FROM article WHERE article_id = {post_id})')
    author_id = mycursor.fetchall()
    author_id = author_id[0][0]

    if author_id == current_user.id:
    
        if request.method == 'POST':
            delete_option = request.form.get('options')
            
            if delete_option == "Yes":
                mycursor.execute(f'DELETE FROM post_tags WHERE article_no = {post_id}')
                mycursor.execute(f'DELETE FROM article WHERE article_id = {post_id}')

                flash("Article Deleted!", "success")
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index'))
        
        else:
            mycursor.execute(f'SELECT title FROM article WHERE article_id = {post_id}')
            post_id = mycursor.fetchall()
            post_id = post_id[0][0]
            return render_template("delete_article.html", post_id = post_id)
        
    else:
        flash("You aren't authorised!", "warning")
        return redirect(url_for('index'))
    
if __name__ == '__main__':
    app.run(debug = True, use_reloader = False, host='localhost', port=5000)