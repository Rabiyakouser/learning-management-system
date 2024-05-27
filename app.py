from flask import Flask, render_template, url_for, request, session, jsonify, redirect
import sqlite3
import secrets
import csv
import string
# import secrets
import os
from datasets import create_dataset
from training import Train
from recognition import Attendence
import pandas as pd
import time
import datetime
from pypdf import PdfReader
import pygame
import time
from gtts import gTTS
from mutagen.mp3 import MP3
import time


con = sqlite3.connect('database.db')
cr = con.cursor()

cr.execute("create table if not exists students(name TEXT, phone TEXT, email TEXT, usn TEXT, sem TEXT, branch TEXT, password TEXT, pysical_disable TEXT, status TEXT)")

cr.execute("create table if not exists teachers(name TEXT, phone TEXT, subject TEXT, email TEXT, password TEXT)")

command = """CREATE TABLE IF NOT EXISTS video (Id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT,  file TEXT)"""
cr.execute(command)

command = """CREATE TABLE IF NOT EXISTS audio (Id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, file TEXT)"""
cr.execute(command)

command = """CREATE TABLE IF NOT EXISTS pdf (Id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, file TEXT)"""
cr.execute(command)

command = """CREATE TABLE IF NOT EXISTS scores (name TEXT, usn TEXT, subject TEXT, score TEXT)"""
cr.execute(command)

import google.generativeai as genai
genai.configure(api_key='AIzaSyAg6UtggTP8rYwWQ-oBhJQf7xDa7SyyhpE')
gemini_model = genai.GenerativeModel('gemini-pro')
chat = gemini_model.start_chat(history=[])

app = Flask(__name__)
chat_history = []
app.secret_key = secrets.token_hex(16)

def generate_password(length):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def getid():
   if not os.path.exists('StudentDetails.csv'):
      return 1
   else:
      df = pd.read_csv('StudentDetails.csv')
      names1 = df['Id'].values
      names1 = list(set(names1))
      return int(names1[-1])+1

@app.route('/create_datsets',  methods=['POST','GET'])
def create_datsets():
   if request.method == 'POST':
      Id = request.form['Id']
      Name = request.form['Name']
      Phone = request.form['Phone']
      Email = request.form['Email']
      Sem = request.form['Sem']
      Cource = request.form['Cource']
      Branch = request.form['Branch']

      print(Id+' '+Name+' '+Phone+' '+Email+' '+Sem+' '+Cource+' '+Branch)

      create_dataset(Id, Name)
      
      msg = ['Images Saved for',
            'ID : ' + Id,
            'Name : ' + Name,
            'Phone : ' + Phone,
            'Email : ' + Email,
            'Semester : ' + Sem,
            'Cource : ' + Cource,
            'Branch : ' + Branch]
      
      row = [Id, Name, Phone, Email, Sem, Cource, Branch]

      if not os.path.exists('StudentDetails.csv'):
         row1 = ['Id', 'Name', 'Phone', 'Email', 'Sem', 'Cource', 'Branch']
         with open('StudentDetails.csv','w',newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row1)
         csvFile.close()

      with open('StudentDetails.csv','a', newline='') as csvFile:
         writer = csv.writer(csvFile)
         writer.writerow(row)
      csvFile.close()

      Train()

      return render_template("attendance.html", msg=msg, ID=getid())
   return render_template("attendance.html", ID=getid())

@app.route('/attendence',  methods=['POST','GET'])
def attendence():
   if request.method == 'POST':
      Subject = request.form['Subject']
      names= Attendence()
      if names == 'unknown':
         return render_template("attendance.html", ID=getid(), msg = ['Unknown person'])
      else:
         df = pd.read_csv('StudentDetails.csv')
         names1 = df['Name'].values
         names1 = list(set(names1))
         
         col_names =  ['Name','Date','Time', 'Status']
         ts = time.time()      
         date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
         timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
         Hour,Minute,Second=timeStamp.split(":")
         fileName="StudentAttendence/"+str(Subject)+"/Attendence_"+date+"_"+Hour+"-"+Minute+"-"+Second+".csv"

         attendence_info = []
         f = open(fileName, 'w', newline='')
         writer = csv.writer(f)
         writer.writerow(col_names)
         
         for name in names1:
            if name in names:
               writer.writerow([name, date, timeStamp, 'Present'])
               attendence_info.append(name+' is Present')
            else:
               writer.writerow([name, date, timeStamp, 'Absent'])
               attendence_info.append(name+' is Absent')
         return render_template("attendance.html", ID=getid(), List=attendence_info,  subject=Subject, date=date, time=timeStamp)
   return render_template("attendance.html", ID=getid())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscrib')
def subscrib():
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    st = 'subscribed'
    cr.execute("update students set status = '"+st+"' where name = '"+session['user']+"'")
    con.commit()
    return render_template('studentlog.html', msg="subscribed successfully")

@app.route('/logout')
def logout():
    return render_template('index.html')

@app.route('/shome')
def shome():
    return render_template('studentlog.html')

@app.route('/certificate/<sub>')
def certificate(sub):
    print(sub)
    import datetime
    Date = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('certificate.html', sub=sub, Date=Date, name=session['user'])

@app.route('/uploadcertificate', methods=['POST', 'GET'])
def uploadcertificate():
    if request.method == 'POST':
        file = request.form['file']
        path = 'static/certificates/'+file
        con = sqlite3.connect('database.db')
        cr = con.cursor()
        cr.execute("update students set pysical_disable = '"+path+"' where name = '"+session['user']+"'")
        con.commit()
        return render_template('studentlog.html', msg = 'certificate file uploaded successfully')
    return render_template('uploadcertificate.html')

@app.route('/material')
def material():
    return render_template('material.html')

@app.route('/adminlog', methods=['GET', 'POST'])
def adminlog():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        if name == 'admin@gmail.com' and password == 'admin123':
            return render_template('add_student.html')
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')
    return render_template('index.html')

@app.route('/studentlog', methods=['GET', 'POST'])
def studentlog():
    if request.method == 'POST':

        con = sqlite3.connect('database.db')
        cr = con.cursor()

        usn = request.form['usn']
        password = request.form['password']

        query = "SELECT * FROM students WHERE usn = '"+usn+"' AND password= '"+password+"'"
        cr.execute(query)

        result = cr.fetchone()

        if result:
            session['user'] = result[0]
            session['usn'] = result[3]
            return render_template('studentlog.html')
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('index.html')

@app.route('/teacherlog', methods=['GET', 'POST'])
def teacherlog():
    if request.method == 'POST':

        con = sqlite3.connect('database.db')
        cr = con.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM teachers WHERE email = '"+email+"' AND password= '"+password+"'"
        cr.execute(query)

        result = cr.fetchall()

        if result:
            return render_template('teacherlog.html')
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('index.html')


@app.route('/add_student', methods=['POST', 'GET'])
def add_student():
    if request.method == 'POST':
        data = request.form

        List = []
        for key in data:
            List.append(data[key])

        con = sqlite3.connect('database.db')
        cr = con.cursor()
        
        query = "SELECT * FROM students where usn = '"+List[3]+"'"
        cr.execute(query)
        result = cr.fetchall()
        if result:
            return render_template('add_student.html', msg="Entered usn number already exists")
        else:
            password = generate_password(8)
            print(password)
            List.append(password)
            cr.execute("insert into students values (?,?,?,?,?,?,?,NULL,NULL)", List)
            con.commit()

            return render_template('add_student.html', msg=f"student data added successfully password is {password}")
    return render_template('add_student.html')

@app.route('/add_teacher', methods=['POST', 'GET'])
def add_teacher():
    if request.method == 'POST':
        data = request.form

        List = []
        for key in data:
            List.append(data[key])

        con = sqlite3.connect('database.db')
        cr = con.cursor()
        
        query = "SELECT * FROM teachers where email = '"+List[3]+"'"
        cr.execute(query)
        result = cr.fetchall()
        if result:
            return render_template('add_student.html', msg="Entered email number already exists")
        else:
            password = generate_password(8)
            print(password)
            List.append(password)

            cr.execute("insert into teachers values (?,?,?,?,?)", List)
            con.commit()

            return render_template('add_teacher.html', msg=f"teacher data added successfully password is {password}")
    return render_template('add_teacher.html')

@app.route('/viewstudents')
def viewstudents():
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    query = "SELECT * FROM students"
    cr.execute(query)
    result = cr.fetchall()
    if result:
        headings = []
        List = cr.execute("select * from students")
        for row in List.description:
            headings.append(row[0])
        return render_template('view_students.html', result=result, headings=headings)
    else:
        return render_template('view_students.html', msg="data not found")

@app.route('/viewteacher')
def viewteacher():
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    query = "SELECT * FROM teachers"
    cr.execute(query)
    result = cr.fetchall()
    if result:
        headings = []
        List = cr.execute("select * from teachers")
        for row in List.description:
            headings.append(row[0])
        return render_template('view_teacher.html', result=result, headings=headings)
    else:
        return render_template('view_teacher.html', msg="data not found")

@app.route('/remove_student/<usn>')
def remove_student(usn):
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    cr.execute("delete from students where usn='"+usn+"'")
    con.commit()
    return redirect(url_for('viewstudents'))

@app.route('/remove_teacher/<email>')
def remove_teacher(email):
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    cr.execute("delete from teachers where email='"+email+"'")
    con.commit()
    return redirect(url_for('viewteacher'))

@app.route('/video', methods=['GET', 'POST'])
def video():
    if request.method == 'POST':
        subject = request.form['subject']
        link = request.form['link']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO video VALUES (NULL, '"+subject+"', '"+link+"')")
        connection.commit()

        return render_template('teacherlog.html')
       
    return render_template('teacherlog.html')

@app.route('/audio', methods=['GET', 'POST'])
def audio():
    if request.method == 'POST':
        subject = request.form['subject']
        file = request.form['file']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO audio VALUES (NULL, '"+subject+"', '"+file+"')")
        connection.commit()

        return render_template('material.html')
       
    return render_template('material.html')

@app.route('/pdf', methods=['GET', 'POST'])
def pdf():
    if request.method == 'POST':
        subject = request.form['subject']
        file = request.form['file']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO pdf VALUES (NULL, '"+subject+"', '"+file+"')")
        connection.commit()

        return render_template('material.html')
       
    return render_template('material.html')

@app.route('/python', methods=['GET', 'POST'])
def python():
    if request.method == 'POST':
        score = 0
        answers = {
            'q1': 'b',
            'q2': 'c',
            'q3': 'a',
            'q4': 'd',
            'q5': 'b',
            'q6': 'c',
            'q7': 'a',
            'q8': 'b',
            'q9': 'c',
            'q10': 'd'
        }
        for question, answer in answers.items():
            user_answer = request.form.get(question)
            if user_answer == answer:
                score += 1
        
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO scores VALUES ('"+session['user']+"', '"+session['usn']+"', 'python', '"+str(score)+"')")
        connection.commit()

        msg =  f'Your score is {score}/10. Thank you for taking the quiz!'

        return render_template('python.html', msg=msg)
    return render_template('python.html')

@app.route('/html', methods=['GET', 'POST'])
def html():
    if request.method == 'POST':
        score = 0
        answers = {
            'q1': 'a',
            'q2': 'a',
            'q3': 'a',
            'q4': 'b',
            'q5': 'b',
            'q6': 'a',
            'q7': 'b',
            'q8': 'a',
            'q9': 'b',
            'q10': 'a'
        }
        for question, answer in answers.items():
            user_answer = request.form.get(question)
            if user_answer == answer:
                score += 1

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO scores VALUES ('"+session['user']+"', '"+session['usn']+"', 'html', '"+str(score)+"')")
        connection.commit()
        
        msg =  f'Your score is {score}/10. Thank you for taking the quiz!'

        return render_template('html.html', msg=msg)
    return render_template('html.html')

@app.route('/css', methods=['GET', 'POST'])
def css():
    if request.method == 'POST':
        score = 0
        answers = {
            'q1': 'c',
            'q2': 'a',
            'q3': 'b',
            'q4': 'd',
            'q5': 'c',
            'q6': 'b',
            'q7': 'a',
            'q8': 'c',
            'q9': 'b',
            'q10': 'a'
        }
        for question, answer in answers.items():
            user_answer = request.form.get(question)
            if user_answer == answer:
                score += 1

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO scores VALUES ('"+session['user']+"', '"+session['usn']+"', 'css', '"+str(score)+"')")
        connection.commit()
        
        msg =  f'Your score is {score}/10. Thank you for taking the quiz!'

        return render_template('css.html', msg=msg)
    return render_template('css.html')

@app.route('/js', methods=['GET', 'POST'])
def js():
    if request.method == 'POST':
        score = 0
        answers = {
            'q1': 'b',
            'q2': 'c',
            'q3': 'a',
            'q4': 'd',
            'q5': 'b',
            'q6': 'c',
            'q7': 'a',
            'q8': 'b',
            'q9': 'c',
            'q10': 'd'
        }
        for question, answer in answers.items():
            user_answer = request.form.get(question)
            if user_answer == answer:
                score += 1
       
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute("INSERT INTO scores VALUES ('"+session['user']+"', '"+session['usn']+"', 'js', '"+str(score)+"')")
        connection.commit()
        
        msg = f'Your score is {score}/10. Thank you for taking the quiz!'

        return render_template('js.html', msg=msg)
    return render_template('js.html')

@app.route('/python_cource')
def python_cource():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM video WHERE subject = 'python'"
    cursor.execute(query)
    video = cursor.fetchall()
    if video:
        return render_template('cources.html', video=video, title="python cources", course='python')
    else:
        return render_template('cources.html', msg='cources not found')

@app.route('/html_cource')
def html_cource():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM video WHERE subject = 'html'"
    cursor.execute(query)
    video = cursor.fetchall()
    if video:
        return render_template('cources.html', video=video, title="html cources", course='python')
    else:
        return render_template('cources.html', msg='cources not found')

@app.route('/css_cource')
def css_cource():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM video WHERE subject = 'css'"
    cursor.execute(query)
    video = cursor.fetchall()
    if video:
        return render_template('cources.html', video=video, title="css cources", course='python')
    else:
        return render_template('cources.html', msg='cources not found')

@app.route('/js_cource')
def js_cource():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM video WHERE subject = 'js'"
    cursor.execute(query)
    video = cursor.fetchall()
    if video:
        return render_template('cources.html', video=video, title="javascript cources", course='python')
    else:
        return render_template('cources.html', msg='cources not found')


@app.route('/python_material')
def python_material():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM pdf WHERE subject = 'python'"
    cursor.execute(query)
    pdf = cursor.fetchall()

    query = "SELECT * FROM audio WHERE subject = 'python'"
    cursor.execute(query)
    audio = cursor.fetchall()

    return render_template('study_materials.html', pdf=pdf, audio=audio, title="python  study material")


@app.route('/html_material')
def html_material():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM pdf WHERE subject = 'html'"
    cursor.execute(query)
    pdf = cursor.fetchall()

    query = "SELECT * FROM audio WHERE subject = 'html'"
    cursor.execute(query)
    audio = cursor.fetchall()

    return render_template('study_materials.html', pdf=pdf, audio=audio, title="html  study material")

@app.route('/css_material')
def css_material():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM pdf WHERE subject = 'css'"
    cursor.execute(query)
    pdf = cursor.fetchall()

    query = "SELECT * FROM audio WHERE subject = 'css'"
    cursor.execute(query)
    audio = cursor.fetchall()

    return render_template('study_materials.html', pdf=pdf, audio=audio, title="css  study material")

@app.route('/js_material')
def js_material():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    query = "SELECT * FROM pdf WHERE subject = 'js'"
    cursor.execute(query)
    pdf = cursor.fetchall()

    query = "SELECT * FROM audio WHERE subject = 'js'"
    cursor.execute(query)
    audio = cursor.fetchall()

    return render_template('study_materials.html', pdf=pdf, audio=audio, title="javascript study material")

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        user_input = request.form['query']
        gemini_response = chat.send_message(user_input + ' explain in few lines')
        data = gemini_response.text
        print(data)
        chat_history.append([user_input, data])
        return render_template('chatbot.html', chat_history=chat_history)
    return render_template('chatbot.html')

@app.route('/score')
def score():
    con = sqlite3.connect('database.db')
    cr = con.cursor()
    query = "SELECT * FROM scores"
    cr.execute(query)
    result = cr.fetchall()
    if result:
        headings = []
        List = cr.execute("select * from scores")
        for row in List.description:
            headings.append(row[0])
        return render_template('score.html', result=result, headings=headings)
    else:
        return render_template('score.html', msg="data not found")

@app.route('/Readfile/<File>')
def Readfile(File):
    path = 'static/pdf/'+File
    print(path)
    
    reader = PdfReader(path) 

    print(len(reader.pages)) 

    i = 0
    j = 0
    while i < len(reader.pages):
        page = reader.pages[i] 

        text = page.extract_text()
        print(text)
        if text:
            j += 1
            myobj = gTTS(text=text, lang='en', slow =False)
            myobj.save("voice.mp3")
            print('\n--------------Playing------------\n')
            song = MP3("voice.mp3")
            pygame.mixer.init()
            pygame.mixer.music.load('voice.mp3')
            pygame.mixer.music.play()
            time.sleep(song.info.length)
            pygame.quit()
            if j > 2:
                break
        i += 1

    return redirect(url_for('js_material'))
    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
