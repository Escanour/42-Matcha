from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import requests
import json
import urllib.request
import datetime
import imghdr
import secrets
#import hashlib, binascii, os
#from flask.ext.bcrypt import Bcrypt

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_googlemaps import GoogleMaps, Map
from datetime import date
from string import *
from flask_socketio import SocketIO, send, emit
from pandas.io.json import json_normalize 
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from six.moves.html_parser import HTMLParser
from flask_wtf.csrf import CSRFProtect
# from flask_wtf.csrf import CSRFError

#from flask_assets import Bundle, Environment



UPLOAD_FOLDER = './static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'd6a06bca34234dce94a5588322a93a7a'
csrf = CSRFProtect(app)


GoogleMaps(app, key="AIzaSyA2gJtaDT29wyGqEPFyu7N_Kp8EpV7qdmA")


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Souhail123@'
app.config['MYSQL_DB'] = 'matcha'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'souhail123razik@gmail.com'
app.config['MAIL_PASSWORD'] = 'uzmddchoclfaqvrw'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

mysql = MySQL(app)

socketio = SocketIO(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])









################################################################################################################################################################################################################################################################################
                                                                                                    #INDEX
################################################################################################################################################################################################################################################################################

# @app.errorhandler(CSRFError)
# def handle_csrf_error(e):
#     return render_template('csrf_error.html', reason=e.description), 400


@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles ORDER BY fram DESC LIMIT 3')
        profiles = cursor.fetchall()

        return render_template('index.html', profiles=profiles)



@app.route('/about')
def about():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        return render_template('About-us.html')


@app.route('/banned')
def banned():
    return render_template('banned.html')



def decode(x):
    html = HTMLParser()
    res = html.unescape(x)

    return res

app.jinja_env.filters['decode'] = decode



################################################################################################################################################################################################################################################################################
                                                                                                    #LOGIN
################################################################################################################################################################################################################################################################################




@app.route('/del_account', methods=['POST', 'GET'])
def del_account():
    if 'loggedin' in session:
        if request.method == 'POST':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('DELETE FROM PROFILES WHERE id_profile = %s', [session['id']])
            mysql.connection.commit()

            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)

            return redirect(url_for('login'))
        else:
            return redirect(url_for('profile'))

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
# @csrf.exempt
def login():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        msg = ''



        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
   

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            
            
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND confirm = 1', [username])
            account = cursor.fetchone()

            cursor.execute('SELECT * FROM profiles WHERE username = %s', [username])
            profile = cursor.fetchone()


            

            if account:
                cursor.execute('SELECT COUNT(*) FROM reports WHERE reported_id = %s', [account['id']])
                reports = cursor.fetchone()
                report = reports['COUNT(*)']

          

                if report >= 5:
                    cursor.execute('UPDATE profiles SET checker = 0 WHERE id_profile = %s', [account['id']])
                    mysql.connection.commit()
                    return redirect(url_for('banned'))
                

                cursor.execute('SELECT password  FROM accounts WHERE username = %s', [username])
                p = cursor.fetchone()
                hashed_password = p['password']
                if check_password_hash(hashed_password, password):
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']

                    cursor.execute("UPDATE n SET log = 1 WHERE id = %s", [account['id']])
                    
                    mysql.connection.commit()

                    # response = requests.get('https://extreme-ip-lookup.com/json/')
                    # js = response.json()
                    # city = js['city']

                    # cursor.execute('UPDATE profiles SET city = %s WHERE id_profile = %s', [city, session['id']])
                    if not profile['age'] == '0' and not profile['gender'] == '0' and not profile['bio'] == '0' and not profile['tags'] == '0' and not profile['img0'] == 'default.png' and not report >= 5:
                        cursor.execute('UPDATE profiles SET checker = 1 WHERE id_profile = %s', [session['id']])
          
                        mysql.connection.commit()
                    else:
                        cursor.execute('UPDATE profiles SET checker = 0 WHERE id_profile = %s', [session['id']])
                        mysql.connection.commit()
                        
                    
                    return redirect(url_for('home'))
                
                                    # Redirect to home page
                        
                else:
                    msg = 'Incorrect username/password!'
            else:
                msg = 'Incorrect username/password!'
            #else:
            # msg = 'Incorrect username/password!'
        return render_template('login.html', msg=msg)



################################################################################################################################################################################################################################################################################
                                                                                                    #LOG_OUT
################################################################################################################################################################################################################################################################################



@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'loggedin' in session:
        if request.method == 'POST':
            time = str(datetime.datetime.now())
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("UPDATE profiles SET timestamp = %s WHERE id_profile = %s", [time, session['id']])
            cursor.execute("UPDATE n SET log = 0 WHERE id = %s", [session['id']])
            mysql.connection.commit()

            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)
            # Redirect to login page
            return redirect(url_for('login'))
        else:
            return redirect(url_for('home'))
    return redirect(url_for('login'))



################################################################################################################################################################################################################################################################################
                                                                                                    #BLOCKED
################################################################################################################################################################################################################################################################################

@app.route('/blocked')
def blocked():
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))

            if not me['checker']==0:

                me = data_prof(session['id'])
                notf = notification(me['id_profile'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM profiles WHERE id_profile != %s', [session['id']])
                profiles = cursor.fetchall()

                cursor.execute("SELECT * FROM block WHERE user_id = %s", [session['id']])
                blocked = cursor.fetchall()
                
                b = []
                for block in blocked:
                    b.append(block['blocked_id'])

                return render_template('blocked.html', profiles=profiles, b=b, me=me, notf=notf, num=num)

            return redirect(url_for('profile'))    
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))


@app.route('/deblock/<int:id_profile>')
def deblock(id_profile):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE id_profile=%s', [id_profile])
        prof = cursor.fetchone()
    
        cursor.execute('DELETE FROM block WHERE user_id = %s AND blocked_id = %s', [session['id'], id_profile])

        prof = prof['fram'] + 25
        fram = str(prof)
        cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
        mysql.connection.commit()
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/report/<int:id_profile>')
def report(id_profile):
    if 'loggedin' in session:
        if id_profile == session['id']:
            return redirect(url_for('home'))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE id_profile=%s', [id_profile])
        prof = cursor.fetchone()
    
        cursor.execute("SELECT * FROM reports WHERE user_id = %s", [session['id']])
        reports = cursor.fetchall()
         
        b = []
        for report in reports:
            b.append(report['reported_id'])

        time = datetime.datetime.now()

        if not id_profile in b:
            cursor.execute("INSERT INTO reports VALUE (NULL, %s, %s, %s)", [session['id'], id_profile, time])

            prof = prof['fram'] - 25
            fram = str(prof)
            cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
            mysql.connection.commit()
            return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    return redirect(url_for('login'))


################################################################################################################################################################################################################################################################################
                                                                                                    #REGISTER
################################################################################################################################################################################################################################################################################


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'name' in request.form and 'surname' in request.form and 'email' in request.form and 'password' in request.form and 'confirm_password' in request.form:
            username = request.form['username']
            name = request.form['name']
            surname = request.form['surname']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            img = 'default.png'

            time = str(datetime.datetime.now())
            pattern = "^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=]).*$"
            
            username_check = re.match(r'[A-Za-z0-9]+', username)
            token = s.dumps(email, salt='email-confirm')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email) or len(email) > 50:
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z]+', username) or len(username) < 2 or len(username) > 10:
                msg = 'Username must be at least 3 characters contain only characters and numbers!'
            elif not re.match(r'[A-Za-z]+', name) or len(name) < 2 or len(name) > 10:
                msg = 'Name must be at least 3 characters contain only characters and numbers!'
            elif not re.match(r'[A-Za-z]+', surname) or len(surname) < 2 or len(surname) > 10:
                msg = 'Surname must be at least 3 characters contain only characters and numbers!'
            elif not re.findall(pattern, password):
                msg = "Password must be contain a number and an uppercase letter ."
            elif (len(password) < 8) or len(password) > 50:
                msg = "Password must be at least 8 characters long"
            elif password != confirm_password:
                msg = 'Passord not same'
            elif not username or not name or not surname or not email or not password or not confirm_password:
                msg = 'Please fill out the form!'
            else:
                response = requests.get('https://extreme-ip-lookup.com/json/')
                js = response.json()
                city = js['city']
                lat = js['lat']
                lon = js['lon']

                password = generate_password_hash(password)

                cursor.execute('INSERT INTO profiles VALUES (NULL, %s, %s, %s, %s, %s, %s, 0, 0, "Bisexual", 0, "Matcha", %s, %s, %s, %s, %s, 0, %s, 0)', [username, name, surname, city, lat, lon, img, img, img, img, img, time])

                cursor.execute('SELECT id_profile FROM profiles WHERE username = %s', [username])
                uid = cursor.fetchone()
                
                cursor.execute('INSERT INTO accounts VALUES (%s, %s, %s, %s, %s, 0)', [uid['id_profile'], username, email, password, token])
                
                
                
                
                
                cursor.execute("INSERT INTO n VALUES (%s, %s, 0, 0)", [uid['id_profile'], username])
                
                mysql.connection.commit()

                

                mg = Message('Confirm Email', sender='matcha@reply.com', recipients=[email])
                link = url_for('confirm_email', token=token, _external=True)
                l = "<a href={}>here<a>".format(link)
                mg.body = 'Thanks for signing up! Mr {} you can confirm from {} '.format(request.form['username'], l)
                mail.send(mg)
                return redirect(url_for('confirmation'))
        elif request.method == 'POST':
            msg = 'Please fill out the form!'

        return render_template('register.html', msg=msg)




@app.route('/confirmation')
def confirmation():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        return render_template('active.html')
################################################################################################################################################################################################################################################################################
                                                                                                    #CONFIRM_EMAIL
################################################################################################################################################################################################################################################################################



# @app.route('/hihi')
# def hihi():
#     today = date.datetime.today()
#     return str(today)

@app.route('/confirm_email/<token>')
def confirm_email(token):
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        try:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM accounts WHERE token = %s', [token])
                data = cursor.fetchone()
                if data['confirm'] == 1:
                    return render_template('token_die.html')
                else:
                    email = s.loads(token, salt='email-confirm')
                    new = secrets.token_urlsafe()
                    cursor.execute('UPDATE accounts SET confirm = 1, token = %s WHERE token = %s', [new, token])
                    mysql.connection.commit()
            except:
                return render_template('invalid_token.html')

            
            
        except SignatureExpired:
            return render_template('token_die.html')
        return render_template('token.html')



################################################################################################################################################################################################################################################################################
                                                                                                    #FORGOT_PASSWORD
################################################################################################################################################################################################################################################################################



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        msg = ''
        if request.method == 'POST' and 'email' in request.form:
            email = request.form['email']
            token = s.dumps(email, salt='change-password')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email = %s', [email])
            account = cursor.fetchone()
            if not account:
                msg = 'Dont exist'
            elif not email:
                msg = 'Please fill out the form!'
            else: 
                mg = Message('Change Password', sender='matcha@reply.com', recipients=[email])
                link = url_for('change_password', token=token, _external=True)
                mg.body = 'You can change your password in this link : {}'.format(link)
                mail.send(mg)
                msg = 'Link was sent !'
        elif request.method == 'POST':
            msg = 'Please fill out the form!'

        return render_template('forgot_password.html', msg=msg)




################################################################################################################################################################################################################################################################################
                                                                                                    #CHANGE_PASSWORD
################################################################################################################################################################################################################################################################################




@app.route('/change_password/<token>', methods=['GET', 'POST'])
def change_password(token):
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        try:
            try:
                msg = ''
                email = s.loads(token, salt='change-password', max_age=500)
                if request.method == 'POST' and 'password' in request.form and 'confirm_password' in request.form :
                    password = request.form['password']
                    confirm_password = request.form['confirm_password']
                    pattern = "^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=]).*$"

                    if not re.findall(pattern, password):
                        msg = "Password must be contain a number and an uppercase letter ."
                    elif password != confirm_password:
                        msg = 'Password not same'
                    else :
                        password = generate_password_hash(password)
                        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                        cursor.execute('UPDATE accounts SET password = %s', [password])
                        mysql.connection.commit()
                        return redirect(url_for('login'))
                elif request.method == 'POST':
                    msg = 'Please fill out the form!'
            except:
                return render_template('invalid_token.html')

        except SignatureExpired:
            return render_template('token_die.html')
        return render_template('change_password.html', msg=msg, token=token)   





################################################################################################################################################################################################################################################################################
                                                                                                    #HOME
################################################################################################################################################################################################################################################################################


def bday(x):
    bday = x.split('-')
    year = int(bday[0])
    month = int(bday[1])
    day = int(bday[2])

    today = date.today()
    age = today.year - year - ((today.month, today.day) < (month, day))

    return age

app.jinja_env.filters['bday'] = bday

def dist(x):
    try:
        me = data_prof(session['id'])
        endpoint = 'https://maps.googleapis.com/maps/api/directions/json?'
        api_key = "AIzaSyA2gJtaDT29wyGqEPFyu7N_Kp8EpV7qdmA"
        origin = me['city']
        destination = x

        nav_request = 'origin={}&destination={}&key={}'.format(origin,destination,api_key)
        request = endpoint + nav_request
        response = urllib.request.urlopen(request).read()
        directions = json.loads(response)
        routes = directions['routes']
        legs = routes[0]['legs']
        dst = legs[0]['distance']['text']
        return dst
    except:
        pass


app.jinja_env.filters['dist'] = dist



def distance(lat, lon):
    me = data_prof(session['id'])
    my_location = (me['lat'], me['lon'])
    profile_location = (lat, lon)
    result = great_circle(my_location, profile_location)
    
    # result = ((lat-me['lat'])*(lat-me['lat'])) + ((lon - me['lon'])*(lon - me['lon']))
    return result

app.jinja_env.filters['distance'] = distance

@app.route('/home', defaults={'page':1}, methods=['GET', 'POST'])
@app.route('/home/<int:page>', methods=['POST', 'GET'])
def home(page):
    
    try:
        if 'loggedin' in session :
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))

            if not me['checker']==0:
                perpage=5
                if page == 1:
                    startat = 0
                else:
                    startat=page*perpage
                
                
            
                me = data_prof(session['id'])
                notf = notification(me['id_profile'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        


                cursor.execute("SELECT * FROM likes WHERE id_src = %s", [session['id']])
                likes = cursor.fetchall()

                cursor.execute("SELECT * FROM block WHERE user_id = %s", [session['id']])
                blocked = cursor.fetchall()

                cursor.execute("SELECT * FROM block WHERE blocked_id = %s", [session['id']])
                blocker = cursor.fetchall()

                cursor.execute('SELECT COUNT(*) FROM reports WHERE reported_id = %s', [session['id']])
                reports = cursor.fetchone()
                report = reports['COUNT(*)']

                cursor.execute('SELECT tags FROM profiles')
                tags = cursor.fetchall()


                b = []
                for block in blocked:
                    b.append(block['blocked_id'])

                bkr = []
                for blk in blocker:
                    bkr.append(blk['user_id'])

                s = []
                for like in likes:
                    s.append(like['id_dst'])

                sug_fage = int(me['age']) - 2
                sug_tage = int(me['age']) + 2


                from_age = request.args.get('from_age', default=sug_fage, type=int)
                to_age = request.args.get('to_age', default=sug_tage, type=str)

                from_fram = request.args.get('from_fram', default=0, type=int)
                to_fram = request.args.get('to_fram', default=1000, type=str)

                from_location = request.args.get('from_location', default=0.0, type=float)
                to_location = request.args.get('to_location', default=20.0, type=float)
        

                sort = request.args.get('sort', default='Sort', type=str)

            

                

                if request.method == 'POST' :
                    from_age = request.form['from_age']
                    to_age = request.form['to_age']

                    from_fram = request.form['from_fram']
                    to_fram = request.form['to_fram']

                    from_location = request.form['from_location']
                    to_location = request.form['to_location']

                    sort = request.form['sort']


                    try:
                        from_age=int(from_age)
                        to_age=int(to_age)

                        from_fram=int(from_fram)
                        to_fram=int(to_fram)

                        from_location=float(from_location)
                        to_location=float(to_location)

                        
                    except ValueError :
                        return redirect(url_for('home'))

                    if from_age < 0:
                        from_age = 0

                    if from_fram < 0:
                        from_fram = 0

                    if from_location < 0:
                        from_location = 0

                    if to_age < 0:
                        to_age = me['age'] + 2
                        
                    if to_fram < 0:
                        to_fram = 1000

                    if to_location < 0:
                        to_location = 20.0

                  




                
                sql = "SELECT * FROM (SELECT profiles.id_profile,111.1111 * DEGREES(ACOS(COS(RADIANS( " + str(me['lat']) + " )) * COS(RADIANS(lat)) * COS(RADIANS( " + str(me['lon']) + " ) - RADIANS(lon)) + SIN(RADIANS( " + str(me['lat']) + " )) * SIN(RADIANS(lat)))) AS km from profiles) as distance inner join profiles on distance.id_profile = profiles.id_profile"

                if me['preferences'] == 'Bisexual':
                    sql += " WHERE profiles.id_profile != " + str(me['id_profile'])

                elif me['preferences'] == 'Heterosexual':
                    sql += " WHERE profiles.id_profile != " + str(me['id_profile']) + " AND gender = 'Female' "

                elif me['preferences'] == 'Homosexual':
                    sql += " WHERE profiles.id_profile != " + str(me['id_profile']) + " AND gender = 'Male' "

                # sql += " AND city = '"+ me['city'] + " '"
                sql += " AND age >= " + str(from_age) + " AND age <= " + str(to_age) 
                sql += " AND fram >= " + str(from_fram) + " AND fram <= " + str(to_fram)
                sql += " AND km >= " + str(from_location) + " AND km <= " + str(to_location)
                sql += " AND ( "

                me_tags = me['tags'].split(',')
                if len(me_tags) == 1:
                        sql += " tags LIKE '%" + me_tags[0] + "%') "
                else:
                    for tag in me_tags:
                        if tag == me_tags[-1]:
                            sql += " tags LIKE '%" + tag + "%') "
                            break
                            
                        else:
                            sql += " tags LIKE '%" + tag + "%' OR "

                if sort == 'Age':
                    sql += " ORDER BY age, km ASC, fram DESC "
                elif sort == 'Fram':
                    sql += " ORDER BY fram DESC, km ASC "
                else:
                    sql += " ORDER BY km ASC, fram DESC"

                sql += " limit " + str(startat) + ',' + str(perpage)

                
                cursor.execute(sql)
                profiles = cursor.fetchall()
        

            

                # if report >= 5:
                #     return render_template('banned.html')
            else:
                return redirect(url_for('profile'))

            return render_template('home.html', page=page, users=users, username=session['username'], profiles = profiles, me=me, notf=notf, likes=likes, s=s, b=b, bkr=bkr, from_age=from_age, to_age=to_age, from_fram=from_fram, to_fram=to_fram, from_location=from_location, to_location=to_location, sort=sort, num=num)
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))




def check_location(dist):
    for s in dist:
        if s == ',':
            result = 0
            break
        else:
            result = 1

app.jinja_env.filters['check_location'] = check_location

def check_tag(profile_tags, me_tags):
    for tag in profile_tags:
        if tag in me_tags:
            a = 1
            break
        else:
            a = 0
    return a

app.jinja_env.filters['check_tag'] = check_tag





@app.route('/<int:id_profile>/<action>')
def like(id_profile, action):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE id_profile=%s', [id_profile])
        prof = cursor.fetchone()
        
        time = datetime.datetime.now()

        if action == 'like':
            cursor.execute("INSERT INTO likes VALUE (NULL, %s, %s, %s)", [session['id'], id_profile, time])
            cursor.execute("INSERT INTO chat VALUE (NULL, %s, %s)", [session['id'], id_profile])
            prof = prof['fram'] + 50
            fram = str(prof)
            cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
            mysql.connection.commit()
        if action == 'unlike':
            cursor.execute('DELETE FROM likes WHERE id_src = %s AND id_dst = %s', [session['id'], id_profile])
            cursor.execute('DELETE FROM likes WHERE id_dst = %s AND id_src = %s', [session['id'], id_profile])
            cursor.execute("DELETE FROM chat WHERE user1_id = %s AND user2_id = %s", [session['id'], id_profile])
            cursor.execute("DELETE FROM chat WHERE user2_id = %s AND user1_id = %s ", [session['id'], id_profile])
            prof = prof['fram'] - 50
            fram = str(prof)
            cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
            mysql.connection.commit()
        return redirect(url_for('home'))
    return redirect(url_for('login'))


################################################################################################################################################################################################################################################################################
                                                                                                    #SEARCH
################################################################################################################################################################################################################################################################################





@app.route('/search', defaults={'page':1}, methods=['GET', 'POST'])
@app.route('/search/<int:page>', methods=['GET', 'POST'])
# @app.route('/search/<int:page>/<int:from_age>/<int:to_age>/<int:from_fram>/<int:to_fram>/<location>/<sort>', methods=['GET', 'POST'])
def search(page):
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))

            if not me['checker']==0:
                perpage=5
                if page == 1:
                    startat = 0
                else:
                    startat=page*perpage

                msg = request.args.get('msg', default='', type=str)

                me = data_prof(session['id'])
                notf = notification(me['id_profile'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM likes WHERE id_src = %s", [session['id']])
                likes = cursor.fetchall()

                cursor.execute("SELECT * FROM block WHERE user_id = %s", [session['id']])
                blocked = cursor.fetchall()

                cursor.execute("SELECT * FROM block WHERE blocked_id = %s", [session['id']])
                blocker = cursor.fetchall()

                cursor.execute('SELECT COUNT(*) FROM reports WHERE reported_id = %s', [session['id']])
                reports = cursor.fetchone()
                report = reports['COUNT(*)']


                cursor.execute("SELECT * FROM profiles")
                pr = cursor.fetchall()

                sg_tag = []

                i = 0
                for p in pr:
                    hs = p['tags'].split(',')
                    for h in hs:
                        if h not in sg_tag and not i == 4:
                            sg_tag.append(h)
                            i += 1

                

                block_table = []
                for block in blocked:
                    block_table.append(block['blocked_id'])

                bkr = []
                for blk in blocker:
                    bkr.append(blk['user_id'])

                like_table = []
                for like in likes:
                    like_table.append(like['id_dst'])

                profiles = None


                # from_age = request.args.get('from_age', default='', type=int)
                from_age = request.args.get('from_age', default='', type=str)
                to_age = request.args.get('to_age', default='', type=str)

                from_fram = request.args.get('from_fram', default='', type=str)
                to_fram = request.args.get('to_fram', default='', type=str)

                from_location = request.args.get('from_location', default='', type=str)
                to_location = request.args.get('to_location', default='', type=str)
        
                location = request.args.get('location', default='', type=str)

                tags = request.args.get('tags', default='', type=str)

                sort = request.args.get('sort', default='--', type=str)

                gender = request.args.get('gender', default='Both', type=str)
                
            
                if request.method == 'POST'  :

                    # if tags == '':
                    #     tags = 'Matcha'
                        
                    from_age = request.form['from_age']
                    to_age = request.form['to_age']

                    from_fram = request.form['from_fram']
                    to_fram = request.form['to_fram']

                    from_location = request.form['from_location']
                    to_location = request.form['to_location']

                    location = request.form['location']

                    tags = request.form['tags']

                    sort = request.form['sort']

                    gender = request.form['gender']

                    if  len(tags) > 100 or len(sort) > 100 or len(gender) > 100:
                            redirect(url_for('search'))

                    # try:
                    #     from_age=int(from_age)
                    #     to_age=int(to_age)

                    #     from_fram=int(from_fram)
                    #     to_fram=int(to_fram)



                        
                    # except ValueError :
                    #     return redirect(url_for('search'))
                    
                if not from_age == '' or not to_age == '' or not from_fram == '' or  not to_fram == '' or  not tags == '' or not from_location == '' or  not to_location == '' or not location == '':
                    sql = "SELECT * FROM (SELECT profiles.id_profile,111.1111 * DEGREES(ACOS(COS(RADIANS( " + str(me['lat']) + " )) * COS(RADIANS(lat)) * COS(RADIANS( " + str(me['lon']) + " ) - RADIANS(lon)) + SIN(RADIANS( " + str(me['lat']) + " )) * SIN(RADIANS(lat)))) AS km from profiles) as distance inner join profiles on distance.id_profile = profiles.id_profile"
                    sql += " WHERE profiles.id_profile != " + str(me['id_profile']) 



                    if gender == 'Male':
                        sql += " AND gender = 'Male' "
                    elif gender == 'Female':
                        sql += " AND gender = 'Female' "

                        


                    if not from_age == '':
                        try:
                            int(from_age)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if int(from_age) < 0:
                            from_age = '0'

                        sql += " AND age >= " + from_age
         
                        

                    if not to_age == '' :
                        try:
                            int(to_age)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if  int(to_age) < 0:
                            to_age = '0'

                        sql += " AND age <= " + to_age
                    


                    if not from_fram == '' :
                        try:
                            int(from_fram)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if int(from_fram) < 0:
                            from_fram = '0'

                        sql += " AND fram >= " + from_fram

                    if not to_fram == '' :
                        try:
                            int(to_fram)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if  int(to_fram) < 0:
                            to_fram = '0'

                        sql += " AND fram <= " + to_fram


                    if not from_location == '' :
                        try:
                            float(from_location)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if float(from_location) < 0:
                            from_location = '0.0'

                        sql += " AND km >= " + from_location

                    if not to_location == '' :
                        try:
                            float(to_location)
                        except  :
                            msg = 'Bas request'
                            return redirect(url_for('search', msg=msg))

                        if float(to_location) < 0:
                            to_location = '0.0'

                        sql += " AND km <= " + to_location

                    if not location == '':
                        sql += " AND city = '" + location + "' "

                    if not tags == '':
                        sql += " AND ( "

                        tgs = tags.split(',')
                        if len(tgs) == 1:
                                sql += " tags LIKE '%" + tgs[0] + "%') "
                        else:
                            for tag in tgs:
                                if tag == tgs[-1]:
                                    sql += " tags LIKE '%" + tag + "%') "
                                    break
                                    
                                else:
                                    sql += " tags LIKE '%" + tag + "%' OR "

                    if sort == 'Age':
                        sql += " ORDER BY age, km ASC, fram DESC "
                    elif sort == 'Fam':
                        sql += " ORDER BY fram DESC, km ASC "
                    else:
                        sql += " ORDER BY km ASC, fram DESC"

                    sql += " limit " + str(startat) + ',' + str(perpage)

                
                    cursor.execute(sql)
                    profiles = cursor.fetchall()

                    # if not tags == '':
                    #     tgs = tags.split(',')

                    # for tag in tgs:
                    #     for profile in profiles:
                    #         p_tag = profile['tags'].split(',')
                    #         if tag in p_tag:
                    #             profile['check_tag'] = 1
                    #         else:
                    #             profile['check_tag'] = 0
            

                    for profile in profiles:
                        if not tags == '':
                            tgs = tags.split(',')
                            
                            p_tag = profile['tags'].split(',')
                            
                            for g in tgs:
                                
                                if g in p_tag:
                                    profile['check_tag'] = 1
                                    break
                                else:
                                    profile['check_tag'] = 0
                        else:
                            profile['check_tag'] = 1

                    # if not tags == '':
                    #         tgs = tags.split(',')
                    #         print(tgs)

                    # for profile in profiles:
                    #     p_tag = profile['tags'].split(',')
                    #     for g in tgs:
                    #         if g in p_tag:
                    #             profile['check_tag'] = 1
                    #         else:
                    #             profile['check_tag'] = 0


                return render_template('search.html', page=page, msg=msg, me=me, profiles = profiles, notf=notf, from_age=from_age, to_age=to_age, from_fram=from_fram, to_fram=to_fram, from_location=from_location, to_location=to_location, location=location, tags=tags, sort=sort, gender=gender, block_table=block_table, bkr=bkr, like_table=like_table, sg_tag=sg_tag, num=num)
            
            return redirect(url_for('profile')) 
        else:
            return redirect(url_for('login'))

    except:
        return redirect(url_for('home'))






################################################################################################################################################################################################################################################################################
 






################################################################################################################################################################################################################################################################################
                                                                                                    #USER
################################################################################################################################################################################################################################################################################


@app.route("/<int:user>", methods=['GET', 'POST'])
def user(user):
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            if user == me['id_profile']:
                return redirect(url_for('profile'))

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))

            if not me['checker']==0:

                me = data_prof(session['id'])
                notf = notification(me['id_profile'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

                cursor.execute("SELECT * FROM block WHERE (user_id = %s AND blocked_id = %s) OR (user_id = %s AND blocked_id = %s)", [session['id'], user, user, session['id']])
                block = cursor.fetchall()

                if not len(block) == 0:
                    return redirect(url_for('home'))

                cursor.execute("SELECT * FROM profiles WHERE id_profile = %s", [user])
                profile = cursor.fetchone()
                cursor.execute("SELECT * FROM likes WHERE id_src = %s AND id_dst = %s", [session['id'], user])
                like = cursor.fetchone()
            
                cursor.execute("SELECT * FROM likes WHERE id_src = %s AND id_dst = %s", [user, session['id']])
                l = cursor.fetchone()
                
            
                cursor.execute("SELECT * FROM likes WHERE id_src = %s AND id_dst = %s", [user, session['id']])
                match = cursor.fetchone()
                cursor.execute('SELECT * FROM chat WHERE user1_id = %s AND user2_id = %s', [session['id'], user])
                chat = cursor.fetchone()
                
                tags = profile['tags'].split(',')
                
                prof = profile['fram'] + 10
                fram = str(prof)
                cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, user])
                mysql.connection.commit()

                return render_template('user.html', users=users, user=user, profile=profile, notf=notf, like=like, match=match, chat=chat, tags=tags, me=me, l=l, num=num)

            return redirect(url_for('profile'))
        return redirect(url_for('home'))
    except:
        return redirect(url_for('home'))

@app.route('/like/<int:id_profile>/<action>')
def like_action(id_profile, action):
    if 'loggedin' in session:
        if id_profile == session['id']:
            return redirect(url_for('home'))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE id_profile=%s', [id_profile])
        prof = cursor.fetchone()
        
        time = datetime.datetime.now()

        if action == 'like':
            cursor.execute("INSERT INTO likes VALUE (NULL, %s, %s, %s)", [session['id'], id_profile, time])
            cursor.execute("INSERT INTO chat VALUE (NULL, %s, %s)", [session['id'], id_profile])
            prof = prof['fram'] + 50
            fram = str(prof)
            cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
            mysql.connection.commit()
            
        if action == 'unlike':
            cursor.execute('DELETE FROM likes WHERE id_src = %s AND id_dst = %s', [session['id'], id_profile])
            cursor.execute('DELETE FROM likes WHERE id_dst = %s AND id_src = %s', [session['id'], id_profile])
            cursor.execute("DELETE FROM chat WHERE user1_id = %s AND user2_id = %s", [session['id'], id_profile])
            cursor.execute("DELETE FROM chat WHERE user2_id = %s AND user1_id = %s ", [session['id'], id_profile])
            prof = prof['fram'] - 50
            fram = str(prof)
            cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
            mysql.connection.commit()
        return redirect(url_for('user', user=id_profile))
    return redirect(url_for('login'))




@app.route('/block/<int:id_profile>')
def block(id_profile):
    if 'loggedin' in session:
        if id_profile == session['id']:
            return redirect(url_for('home'))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE id_profile=%s', [id_profile])
        prof = cursor.fetchone()
    
        time = datetime.datetime.now()

        cursor.execute("INSERT INTO block VALUE (NULL, %s, %s, %s)", [session['id'], id_profile, time])
        cursor.execute('DELETE FROM likes WHERE id_src = %s AND id_dst = %s', [session['id'], id_profile])
        cursor.execute('DELETE FROM likes WHERE id_dst = %s AND id_src = %s', [session['id'], id_profile])
        cursor.execute("DELETE FROM chat WHERE user1_id = %s AND user2_id = %s", [session['id'], id_profile])
        cursor.execute("DELETE FROM chat WHERE user2_id = %s AND user1_id = %s ", [session['id'], id_profile])

        prof = prof['fram'] - 25
        fram = str(prof)
        cursor.execute("UPDATE profiles SET fram = %s WHERE id_profile = %s", [fram, id_profile])
        mysql.connection.commit()
        return redirect(url_for('home'))
    return redirect(url_for('login'))




################################################################################################################################################################################################################################################################################
                                                                                                    #PROFILE
################################################################################################################################################################################################################################################################################

def get_city(lat, lon):
    geolocator=Nominatim(timeout=3)
    cor = str(lat) + ',' + str(lon)
    location = geolocator.reverse(cor)
    return location.raw



@app.route('/profile', methods=['GET', 'POST'])
def profile():
    try:
        if 'loggedin' in session:
            
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))


            notf = notification(me['id_profile'])
            n = n_notf(session['id'])
            num = n['num']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT * FROM profiles WHERE id_profile != %s", [session['id']])
            pr = cursor.fetchall()

            sg_tag = []

            i = 0
            for p in pr:
                hs = p['tags'].split(',')
                for h in hs:
                    if h not in sg_tag and not i == 4:
                        sg_tag.append(h)
                        i += 1


            cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
            account = cursor.fetchone()
            cursor.execute('SELECT * FROM profiles WHERE id_profile = %s', [session['id']])
            profile = cursor.fetchone()

        
            msg = ''
            if request.method == 'GET' :
                msg = request.args.get('msg', default='', type=str)
        
            if request.method == 'POST' :
                username = request.form['username']

                for pfile in pr:
                    if pfile['username'] == username and not me['username'] == username:
                        username = me['username']
                        msg = 'username exist'

                full_name = request.form['full_name']


                
                try:
                    full_name = full_name.split(' ')
                    name = full_name[0]
                    surname = full_name[1]

                    if not re.match(r'[A-Za-z]+', name) or len(name) < 2 or len(name) > 20:
                        msg = 'Incorrect name'
                    if not re.match(r'[A-Za-z]+', surname) or len(surname) < 2 or len(surname) > 20:
                        msg = 'Incorrect surname'
                except:
                    name = me['name']
                    surname = me['surname']
                    msg='Invalid Full name'



                email = request.form['email']

                age = request.form['bday']
                
                if age == '':
                    age = me['age']
                else:
                    age = bday(age)
                    if age < 16 or age > 200:
                        age = ''

                if age == '':
                    age = me['age']

                
                
                # bday = bday.split('-')
                # year = int(bday[0])
                # month = int(bday[1])
                # day = int(bday[2])

                # today = date.today()
                # age = today.year - year - ((today.month, today.day) < (month, day))

                gender = request.form['gender']

                if not gender == 'Male' or gender == 'Female':
                    gender = me['gender']

                preferences = request.form['preferences']
                if not preferences == 'Bisexual' or preferences == 'Heterosexual' or preferences == 'Homosexual':
                    preferences = me['preferences']


                lat = request.form['lat']
                lon = request.form['lon']
                
                try:
                    lt = float(lat)
                    ln = float(lon)
                except :
                    lat = me['lat']
                    lon = me['lon']
                    msg = "bad request"
                    return redirect(url_for('profile', msg=msg))

                try:
                    c = get_city(lat, lon)
                    c = c['address']['county'].split(' ')
                    city = c[0]
                except:
                    lat = me['lat']
                    lon = me['lon']
                    city  = me['city']
                    msg = 'Something happen Try again'
            
                # url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + lat + "," + lon + "&key=AIzaSyA2gJtaDT29wyGqEPFyu7N_Kp8EpV7qdmA&sensor=false"
                # response = requests.get(url)
                # js = response.json()
                # city = js.results[2].formatted_address
                # print(city)

                tags = request.form['tags']
            
                bio = request.form['bio']
                if bio == '':
                    bio = me['bio']
                


                if not re.match(r'[A-Za-z]+', username) or len(username) < 2 or len(username) > 10:
                    msg = 'Incorrect username'
                elif not re.match(r'[A-Za-z]+', name) or len(name) < 2 or len(name) > 10:
                    msg = 'Name must be at least 3 characters contain only characters and numbers!'
                elif not re.match(r'[A-Za-z]+', surname) or len(surname) < 2 or len(surname) > 10:
                    msg = 'Surname must be at least 3 characters contain only characters and numbers!'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email) or len(email) > 50:
                    msg = 'Invalid email address!'
                # elif not re.match(r'[A-Za-z]+', city) or len(city) < 2 or len(city) > 20:
                #     msg = 'Incorrect location'
                
                elif not re.match(r'[A-Za-z]+', bio) or len(bio) < 2 or len(bio) > 60:
                    msg = 'Incorrect bio'
                
                
                else:
                    cursor.execute('UPDATE accounts SET username = %s, email = %s WHERE id = %s ', [username, email, session['id']])
                    cursor.execute("UPDATE profiles SET username = %s, name = %s, surname = %s, age = %s, gender = %s, preferences = %s, city = %s, lat = %s, lon = %s, bio = %s WHERE id_profile = %s", [username, name, surname, age, gender, preferences, city, lat, lon, bio, session['id']])
                    if not tags == '':
                        if not re.match(r'[A-Za-z]+', tags) or len(tags) < 2 or len(tags) > 20:
                            msg = 'Incorrect tags'
                        else:
                            cursor.execute("UPDATE profiles SET tags = concat(tags,',',%s) WHERE id_profile = %s", [tags, session['id']])
                            mysql.connection.commit()


                if 'current-password' in request.form and 'new-password' in request.form and 'new-password1' in request.form :
                    pattern = "^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=]).*$"

                    old_psswd = request.form['current-password']
                    new_psswd = request.form['new-password']
                    cnfrm_psswd = request.form['new-password1']
                    


                    if not old_psswd == '':
                        if not re.findall(pattern, new_psswd):
                            msg = "Password must be contain a number and an uppercase letter ."
                        elif not (len(new_psswd) > 8 and len(new_psswd) < 50):
                            msg = "Password must be at least 8 characters long"

                        else:
                            cursor.execute('SELECT password  FROM accounts WHERE id  = %s', [session['id']])
                            p = cursor.fetchone()
                            hashed_password = p['password']

                            if check_password_hash(hashed_password, old_psswd) and new_psswd == cnfrm_psswd:
                                new_psswd = generate_password_hash(new_psswd)
                                cursor.execute("UPDATE accounts SET password = %s WHERE id = %s", [new_psswd, session['id']])
                                mysql.connection.commit()
                                msg = 'Password Set !'
                            else:
                                msg = 'Wrong Password !'
                else:
                    msg = 'Please fill out the form!'

                        
    


                
                # redirect(url_for('profile'))
            
            
            if not profile['age'] == '0' and not profile['gender'] == '0' and not profile['bio'] == '0' and not profile['tags'] == '0' and not profile['img0'] == 'default.png':
                cursor.execute('UPDATE profiles SET checker = 1 WHERE id_profile = %s', [session['id']])
                mysql.connection.commit()
            else:
                cursor.execute('UPDATE profiles SET checker = 0 WHERE id_profile = %s', [session['id']])
                mysql.connection.commit()
            return render_template('profile.html', account=account, profile=profile, me=me, notf=notf, msg=msg, num=num, sg_tag=sg_tag)
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))



    


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route("/imgz", methods=['GET', 'POST'])
def img0():
    if 'loggedin' in session:
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):    
                time = str(datetime.datetime.now())
                time = time.replace(' ', '')
                time = time.replace(':', '')

                filename = secure_filename(photo.filename)  
                photo.filename = time + photo.filename
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
                img = photo.filename
                u = 'static/img/' + img
                p = imghdr.what(u)
                if not p == None:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('UPDATE profiles SET img0 = %s WHERE id_profile = %s', [img, session['id']])
                    mysql.connection.commit()
                else:
                    return redirect(url_for('profile'))
       
        return redirect(url_for('profile'))
    return redirect(url_for('login'))



@app.route("/imgo", methods=['GET', 'POST'])
def img1():
    if 'loggedin' in session:
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):    
                filename = secure_filename(photo.filename)        
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
                img = photo.filename
                u = 'static/img/' + img
                p = imghdr.what(u)
                if not p == None:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('UPDATE profiles SET img1 = %s WHERE id_profile = %s', [img, session['id']])
                    mysql.connection.commit()
                else:
                    return redirect(url_for('profile'))
                
        return redirect(url_for('profile'))
    return redirect(url_for('login'))
    

@app.route("/imgt", methods=['GET', 'POST'])
def img2():
    if 'loggedin' in session:
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):    
                filename = secure_filename(photo.filename)        
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
                img = photo.filename
                u = 'static/img/' + img
                p = imghdr.what(u)
                if not p == None:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('UPDATE profiles SET img2 = %s WHERE id_profile = %s', [img, session['id']])
                    mysql.connection.commit()
                else:
                    return redirect(url_for('profile'))
                
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route("/imgth", methods=['GET', 'POST'])
def img3():
    if 'loggedin' in session:
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):    
                filename = secure_filename(photo.filename)        
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
                img = photo.filename
                u = 'static/img/' + img
                p = imghdr.what(u)
                if not p == None:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('UPDATE profiles SET img3 = %s WHERE id_profile = %s', [img, session['id']])
                    mysql.connection.commit()
                else:
                    return redirect(url_for('profile'))
                
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route("/imgf", methods=['GET', 'POST'])
def img4():
    if 'loggedin' in session:
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):    
                filename = secure_filename(photo.filename)        
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
                img = photo.filename
                u = 'static/img/' + img
                p = imghdr.what(u)
                if not p == None:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('UPDATE profiles SET img4 = %s WHERE id_profile = %s', [img, session['id']])
                    mysql.connection.commit()
                else:
                    return redirect(url_for('profile'))
                
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route("/imgdelz", methods=['GET', 'POST'])
def imgdelz():
    if 'loggedin' in session:
        img = 'default.png'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE profiles SET img0 = %s WHERE id_profile = %s', [img, session['id']])
        mysql.connection.commit()
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route("/imgdelo", methods=['GET', 'POST'])
def imgdelo():
    if 'loggedin' in session:
        img = 'default.png'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE profiles SET img1 = %s WHERE id_profile = %s', [img, session['id']])
        mysql.connection.commit()
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route("/imgdelt", methods=['GET', 'POST'])
def imgdelt():
    if 'loggedin' in session:
        img = 'default.png'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE profiles SET img2 = %s WHERE id_profile = %s', [img, session['id']])
        mysql.connection.commit()
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route("/imgdelth", methods=['GET', 'POST'])
def imgdelth():
    if 'loggedin' in session:
        img = 'default.png'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE profiles SET img3 = %s WHERE id_profile = %s', [img, session['id']])
        mysql.connection.commit()
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route("/imgdelf", methods=['GET', 'POST'])
def imgdelf():
    if 'loggedin' in session:
        img = 'default.png'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE profiles SET img4 = %s WHERE id_profile = %s', [img, session['id']])
        mysql.connection.commit()
        return redirect(url_for('profile'))
    return redirect(url_for('login'))





################################################################################################################################################################################################################################################################################
                                                                                                    #FUNCTIONS
################################################################################################################################################################################################################################################################################


def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
    
def verify_password(stored_password, provided_password):
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def data_prof(x):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM profiles WHERE id_profile = %s', [x])
    data_prof = cursor.fetchone()
    return data_prof



def htmlspecialchars(text):
    return (
        text.replace("&", "&amp;").
        replace('"', "&quot;").
        replace("<", "&lt;").
        replace(">", "&gt;")
    )



################################################################################################################################################################################################################################################################################
                                                                                                    #CHAT
################################################################################################################################################################################################################################################################################
users = {}





@app.route('/friends')
def friends():
    try:

        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))

            if not me['checker']==0:

                me = data_prof(session['id'])
                notf = notification(me['id_profile'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM profiles WHERE id_profile != %s', [session['id']])
                profiles = cursor.fetchall()

                cursor.execute('SELECT * FROM chat WHERE user1_id = %s', [session['id']])
                chat = cursor.fetchone()

                cursor.execute('SELECT * FROM chat WHERE user1_id = %s', [session['id']])
                friends = cursor.fetchall()

                cursor.execute('SELECT * FROM chat WHERE user2_id = %s', [session['id']])
                match = cursor.fetchall()
                
                b = []
                for friend in friends:
                    for m in match:
                        if str(friend['user2_id']) in str(m['user1_id']):
                            b.append(friend['user2_id'])

                

            

                return render_template('friends.html', profiles=profiles, notf=notf, b=b, chat=chat, me=me, num=num)

            return redirect(url_for('profile')) 
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))


@app.route('/chat/<user>', methods=['POST', 'GET'])
def chat(user):
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))


            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

      


            notf = notification(me['id_profile'])
            n = n_notf(session['id'])
            num = n['num']
            log = n['log']

            if not me['checker']==0:

                me = data_prof(session['id'])

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

                cursor.execute('SELECT * FROM messages ')
                messages = cursor.fetchall()

                cursor.execute('SELECT * FROM profiles WHERE username = %s', [user])
                profile = cursor.fetchone()

                cursor.execute("SELECT * FROM likes WHERE (id_src = %s AND id_dst = %s) OR (id_src = %s AND id_dst = %s) ", [session['id'], profile['id_profile'], profile['id_profile'], session['id']])
                like = cursor.fetchall()

                if not len(like) == 2:
                    return redirect(url_for('home'))


                #time = messages['timestamp']

                # time = time.strftime("%H-%M-%S {%d/%B/%Y}")

                return render_template('chat.html', user=user, users=users, profile=profile, me=me, messages=messages, notf=notf, num=num, log=log)
            
            return redirect(url_for('profile'))
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))




@socketio.on('username', namespace='/private')
def receive_username(username):
    if 'loggedin' in session:
        users[username] = request.sid
    return redirect(url_for('login'))


@socketio.on('username_pop', namespace='/private')
def disconnectf(data):
    recipient_session_id = users[data['username']]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    cursor.execute("UPDATE n SET log = 0 WHERE username = %s", [data['username']])
    mysql.connection.commit()

    cursor.execute("SELECT * FROM n WHERE username = %s", [data['username']])
    n = cursor.fetchone()

    log = n['log']


    # emit('out' , {'msg': log}, room=recipient_session_id)
    users.pop(data['username'])
 


@socketio.on('private_message', namespace='/private')
def private_message(payload):
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                recipient_session_id = users[payload['username']]
            except:
                recipient_session_id = 0
                
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM profiles WHERE username = %s',[payload['username']])
            profile = cursor.fetchone()
            cursor.execute('SELECT * FROM chat WHERE user1_id = %s',[profile['id_profile']])
            chat = cursor.fetchone()
            
            cursor.execute("SELECT * FROM n WHERE username = %s", [payload['username']] )
            n = cursor.fetchone()

            new_n = n['num'] + 1

            cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [payload['username']]])

            message = payload['message']

            msg = '{} : '.format(me['username'])+ message
            

            time = str(datetime.datetime.now())

            link = "http://127.0.0.1:5000/chat/" + me['username'] 

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO messages VALUE (NULL, %s, %s, %s, %s, %s, %s)', [me['id_profile'], payload['id'], me['username'], payload['username'], payload['message'], time])
            cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], msg, link, time])
            mysql.connection.commit()
            #print(users[payload['username']])

            emit('new_private_message' , {'msg': msg, 'message': message, 'time': time, 'link': link, 'user' : me['username']}, room=recipient_session_id)
        return redirect(url_for('login'))
    except:
        return redirect(url_for('friends'))

 
    #emit('receivet', {'msg': message, 'me': me['username']} )

   
   




@socketio.on('liked', namespace='/private')
def liked(data):
    if 'loggedin' in session:
        try:
            recipient_session_id = users[data['liked']]
        except:
            recipient_session_id = 0
        me = data_prof(session['id'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE username = %s',[data['liked']])
        profile = cursor.fetchone()

        cursor.execute("SELECT * FROM n WHERE username = %s", [data['liked']] )
        n = cursor.fetchone()

        try:
            new_n = n['num'] + 1
        except:
            return redirect(url_for('home'))

        cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [data['liked']]])

        cursor.execute("SELECT * FROM likes WHERE id_src = %s AND id_dst = %s", [profile['id_profile'], me['id_profile']])
        like = cursor.fetchone()

        if not like == None:
            message = 'You and {} are Matched ! '.format(data['liker'])
        else:
            message = '{} Liked You '.format(data['liker'])

        time = str(datetime.datetime.now())

        link = "http://127.0.0.1:5000/" + str(me['id_profile'])
    
        cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], message, link, time])
        mysql.connection.commit()
        emit('like', {'msg': message, 'time': time, 'link': link}, room=recipient_session_id)
    return redirect(url_for('login'))


@socketio.on('unliked', namespace='/private')
def unliked(data):
    if 'loggedin' in session:
        try:
            recipient_session_id = users[data['unliked']]
        except:
            recipient_session_id = 0
        me = data_prof(session['id'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE username = %s',[data['unliked']])
        profile = cursor.fetchone()

        cursor.execute("SELECT * FROM n WHERE username = %s", [data['unliked']] )
        n = cursor.fetchone()

        try:
            new_n = n['num'] + 1
        except:
            return redirect(url_for('home'))

        cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [data['unliked']]])

        message = '{} Unliked You '.format(data['unliker'])

        time = str(datetime.datetime.now())

        link = "http://127.0.0.1:5000/" + str(me['id_profile'])
    
        cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], message, link, time])
        mysql.connection.commit()
        emit('unlike', {'msg': message, 'time': time, 'link': link}, room=recipient_session_id)
    return redirect(url_for('login'))

@socketio.on('visite', namespace='/private')
def visit(data):
    if 'loggedin' in session:
        try:
            recipient_session_id = users[data['visiter']]
        except:
            recipient_session_id = 0
        me = data_prof(session['id'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE username = %s',[data['visiter']])
        profile = cursor.fetchone()

    

        cursor.execute("SELECT * FROM n WHERE username = %s", [data['visiter']] )
        n = cursor.fetchone()

        try:
            new_n = n['num'] + 1
        except:
            return redirect(url_for('home'))

        cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [data['visiter']]])
    

        message = '{} Visit Your Profile '.format(data['visited'])

        time = str(datetime.datetime.now())

        link = "http://127.0.0.1:5000/" + str(me['id_profile'])

        cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], message, link, time])
        mysql.connection.commit()

        

        emit('vst', {'msg': message, 'time': time, 'link': link}, room=recipient_session_id)
    return redirect(url_for('login'))

# @socketio.on('mcha', namespace='/private')
# def jkj(kk):
#     #print(kk)


@socketio.on('rmv_tag', namespace='/private')
def rmv_tag(data):
    if 'loggedin' in session:
        me = data_prof(session['id'])
        tags = me['tags']

        tags = tags.split(',')

        tg = data['tg'][1:] 

        

        new_tags = ''

        for tag in tags:
            if not tag == tg:
            
                new_tags = new_tags + ',' +tag
            

        new_tags = new_tags[1:]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE profiles SET tags = %s WHERE id_profile = %s", [new_tags, session['id']])
        mysql.connection.commit()
    return redirect(url_for('login'))


@socketio.on('google_location', namespace='/private')
def g_l(data):
    if 'loggedin' in session:
        me = data_prof(session['id'])

        lat = data['lat']
        lon = data['lon']

        c = get_city(lat, lon)
        c = c['address']['city'].split(' ')
        city = str(c[0])
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE profiles SET city = %s , lat = %s , lon = %s WHERE id_profile = %s", [city, lat, lon, session['id']])
        mysql.connection.commit()
        emit('g_rcv', {'msg': 'Your City is Updated :D'})
    return redirect(url_for('login'))


@socketio.on('block', namespace='/private')
def block_notif(data):
    if 'loggedin' in session:
        try:
            recipient_session_id = users[data['blocked']]
        except:
            recipient_session_id = 0
        me = data_prof(session['id'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE username = %s',[data['blocked']])
        profile = cursor.fetchone()

        cursor.execute("SELECT * FROM n WHERE username = %s", [data['blocked']] )
        n = cursor.fetchone()

        try:
            new_n = n['num'] + 1
        except:
            return redirect(url_for('home'))

        cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [data['blocked']]])
        
        message = '{} Blocked You '.format(data['blocker'])

        time = str(datetime.datetime.now())

        link = "#"

    
        cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], message, link, time])
        mysql.connection.commit()
        emit('blck_ntf', {'msg': message, 'time': time, 'link': link}, room=recipient_session_id)
    return redirect(url_for('login'))



@socketio.on('report', namespace='/private')
def report_ntf(data):
    if 'loggedin' in session:
        try:
            recipient_session_id = users[data['reported']]
        except:
            recipient_session_id = 0
        me = data_prof(session['id'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE username = %s',[data['reported']])
        profile = cursor.fetchone()

        cursor.execute("SELECT * FROM n WHERE username = %s", [data['reported']] )
        n = cursor.fetchone()

        try:
            new_n = n['num'] + 1
        except:
            return redirect(url_for('home'))

        cursor.execute("UPDATE n SET num = %s WHERE username = %s", [new_n, [data['reported']]])

        message = '{} Reported You As Fake '.format(data['reporter'])

        time = str(datetime.datetime.now())

        link = "http://127.0.0.1:5000/" + str(me['id_profile'])

        cursor.execute('INSERT INTO notf VALUE (NULL, %s, %s, %s, %s)', [profile['id_profile'], message, link, time])
        mysql.connection.commit()
        emit('rprt_ntf', {'msg': message, 'time': time, 'link': link}, room=recipient_session_id)
    return redirect(url_for('login'))


def notification(x):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM notf WHERE user_id = %s ORDER BY timestamp DESC', [x])
    notf = cursor.fetchall()
    return notf



@app.route('/notf')
def notf():
    try:
        if 'loggedin' in session:
            me = data_prof(session['id'])

            try:
                test = me['checker']
            except:
                return redirect(url_for('logout'))


            if not me['checker']==0:

                me = data_prof(session['id'])
                n = n_notf(session['id'])
                num = n['num']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM profiles WHERE id_profile = %s',[session['id']])
                profile = cursor.fetchone()
                cursor.execute('SELECT * FROM notf WHERE user_id = %s ORDER BY timestamp DESC', [session['id']])
                notf = cursor.fetchall()



                return render_template('notf.html', me=me, notf=notf, profile=profile, num=num)

            return redirect(url_for('profile')) 
        return redirect(url_for('login'))
    except:
        return redirect(url_for('home'))


@socketio.on('clear', namespace='/private')
def clear(data):
    if 'loggedin' in session:
        recipient_session_id = users[data['username']]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM notf WHERE user_id = %s', [data['id']])
        mysql.connection.commit()
    return redirect(url_for('login'))



@socketio.on('c_n', namespace='/private')
def c_n(data):
    if 'loggedin' in session:
        recipient_session_id = users[data['username']]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE n SET num = 0 WHERE id = %s", [data['id']])
        mysql.connection.commit()
    return redirect(url_for('login'))



    

################################################################################################################################################################################################################################################################################
                                                                                                    #TESSSST
################################################################################################################################################################################################################################################################################

##############################################################################################################################################################################################################################################################################




def n_notf(user):

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM n WHERE id = %s", [user])
    n = cursor.fetchone()

    return n

@app.route('/log')
def log():
    try:
        if 'loggedin' in session:
            n = n_notf(session['id'])
            log = str(n['log'])
            return render_template('log.html', log=log)
        return redirect(url_for('login'))
    except:
        log = 0
        return log



##############################################################################################################################################################################################################################################################################


################################################################################################################################################################################################################################################################################
                                                                                                    #APP.RUN
################################################################################################################################################################################################################################################################################



if __name__ == "__main__":
    socketio.run(app, debug=True)
    

