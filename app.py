from flask import Flask, render_template, request, redirect, url_for, session, flash,send_from_directory
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
import random
import time
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
import bcrypt
import json
from json import JSONDecodeError
import os
import fitz 
import re
# import spacy
# nlp = spacy.load("en_core_web_sm")
# from pyresparser import ResumeParser

# Langchain & Groq modules
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECTNAME"] = os.getenv("LANGCHAIN_PROJECTNAME")
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#Modules for Database
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = 'your-secret-key'

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jayanthi@21'
app.config['MYSQL_DB'] = 'ATP'
mysql = MySQL(app)

# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ats.service1234@gmail.com'  
app.config['MAIL_PASSWORD'] = 'zkke tflj keai lzai'  # use app password or environment variable
app.config['MAIL_DEFAULT_SENDER'] = 'ats.service1234@gmail.com'
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

# Helper function to send email with error handling
def send_email(subject, recipients, body):
    try:
        msg = Message(subject, recipients=recipients)
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/jobseeker_auth')
def jobseeker_auth():
    if session.get('js_id'):
        return redirect(url_for('job_seeker'))  
    return render_template('jobseeker_auth.html')


@app.route('/recruiter_auth')
def recruiter_auth():
    if session.get('recruiter_id'):
        return redirect(url_for('recruiter_analyser'))  
    return render_template('recruiter_auth.html')


@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT js_id FROM job_seeker WHERE js_email = %s", (email,))
    existing = cur.fetchone()
    cur.close()

    if existing:
        flash("Email already registered. Please log in.", "warning")
        return redirect(url_for('jobseeker_auth'))

    hashed_password = generate_password_hash(password)
    otp = str(random.randint(100000, 999999))
    session['signup_data'] = {
        'email': email,
        'password': hashed_password,
        'otp': otp,
        'timestamp': time.time(),
        'last_otp_sent': time.time()
    }

    if send_email('Your OTP for Signup', [email], f'Your OTP is: {otp}'):
        flash("OTP sent to your email.", "info")
    else:
        flash("Failed to send OTP. Please try again later.", "danger")
        return redirect(url_for('jobseeker_auth'))

    return redirect(url_for('verify_otp'))

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    signup_data = session.get('signup_data')

    if not signup_data:
        flash("Session expired. Please start signup again.", "danger")
        return redirect(url_for('jobseeker_auth'))

    MAX_OTP_AGE = 300  # 5 minutes

    if request.method == 'POST':
        entered_otp = request.form['otp'].strip()

        if time.time() - signup_data.get('timestamp', 0) > MAX_OTP_AGE:
            session.pop('signup_data', None)
            flash("OTP expired. Please sign up again.", "warning")
            return redirect(url_for('jobseeker_auth'))

        if entered_otp == signup_data.get('otp'):
            email = signup_data['email']
            password = signup_data['password']

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO job_seeker (js_email, js_password)
                VALUES (%s, %s)
            """, (email, password))
            mysql.connection.commit()
            cur.close()

            session.pop('signup_data', None)
            flash("Signup successful. Please log in.", "success")
            return redirect(url_for('jobseeker_auth'))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template('verify_otp.html')

@app.route('/resend_otp')
def resend_otp():
    signup_data = session.get('signup_data')

    if not signup_data:
        flash("Session expired. Please start signup again.", "danger")
        return redirect(url_for('jobseeker_auth'))

    # Cooldown: allow resend only if 30 seconds have passed since last OTP sent
    last_sent = signup_data.get('last_otp_sent', 0)
    if time.time() - last_sent < 30:
        flash("Please wait before resending OTP again.", "warning")
        return redirect(url_for('verify_otp'))

    new_otp = str(random.randint(100000, 999999))
    signup_data['otp'] = new_otp
    signup_data['timestamp'] = time.time()
    signup_data['last_otp_sent'] = time.time()
    session['signup_data'] = signup_data

    if send_email('Your New OTP for Signup', [signup_data['email']], f'Your new OTP is: {new_otp}'):
        flash("A new OTP has been sent to your email.", "info")
    else:
        flash("Failed to send OTP. Please try again later.", "danger")

    return redirect(url_for('verify_otp'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM job_seeker WHERE js_email = %s", (email,))
    user = cur.fetchone()#user is tuple here
    cur.close()
    if user and check_password_hash(user[2], password):
        session['user'] = email
        session['js_id']=user[0]
        flash("Logged in successfully.", "success") 
        return redirect(url_for('job_seeker'))
    else:
        flash("Invalid credentials", "danger")
        return redirect(url_for('jobseeker_auth'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Get the email from query param if exists (email typed on login)
    login_email = request.args.get('email', '').strip()

    if request.method == 'POST':
        email_entered = request.form['email'].strip()

        # Check if email entered matches login_email (if login_email provided)
        if login_email and email_entered != login_email:
            flash("Email entered does not match the email from the login page.", "danger")
            return render_template('forgot_password.html', email=email_entered)

        
        cur = mysql.connection.cursor()
        cur.execute("SELECT js_id FROM job_seeker WHERE js_email = %s", (email_entered,))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("Email not found.", "danger")
            return render_template('forgot_password.html', email=email_entered)

        token = serializer.dumps(email_entered, salt='reset-password')
        link = url_for('reset_password', token=token, _external=True)

        if send_email("Reset Your Password", [email_entered], f"Click the link to reset your password: {link}"):
            flash("Password reset link sent to your email.", "info")
            return redirect(url_for('jobseeker_auth'))
        else:
            flash("Failed to send reset email. Please try again later.", "danger")
            return render_template('forgot_password.html', email=email_entered)

    return render_template('forgot_password.html', email=login_email)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Link expired or invalid.", "danger")
        return redirect(url_for('jobseeker_auth'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('reset_password', token=token))

        hashed = generate_password_hash(new_password)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE job_seeker SET js_password = %s WHERE js_email = %s", (hashed, email))
        mysql.connection.commit()
        cur.close()

        session['user'] = email
        flash("Password reset successful.", "success")
        return redirect(url_for('jobseeker_auth'))

    return render_template('reset_password.html')

def verify_recruiter(email,groq_api_key):
            llm = ChatGroq(model='gemma2-9b-it', groq_api_key=groq_api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert recruiter email analyser.
                        Only respond with 'yes' or 'no'. Do not explain anything.
                        Check if the given email is a recruiter or HR email of a company.
                 **Remember provide only 'yes' or 'no' as output."""),
                ("user", "Question:{question}")
            ])
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser
            
            response = chain.invoke({
                "question": email
            })
            return response


@app.route('/recruiter_signup', methods=['POST'])
def recruiter_signup():
    email = request.form['email']
    password = request.form['password']
    if not email or not password:
        flash("Please fill all fields.", "danger")
        return redirect(url_for('recruiter_auth'))
    try:
        response = verify_recruiter(email, groq_api_key).lower()
    except Exception as e:
        app.logger.error(f"Recruiter verification failed: {e}")
        flash("Verification service error. Please try again.", "danger")
        return redirect(url_for('recruiter_auth'))
    if response.strip()=='yes':
        cur = mysql.connection.cursor()
        cur.execute("SELECT recruiter_id FROM recruiter WHERE recruiter_email = %s", (email,))
        existing = cur.fetchone()
        cur.close()

        if existing:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('recruiter_auth'))

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(100000, 999999))
        session['recru_signup_data'] = {
            'email': email,
            'password': hashed_password,
            'otp': otp,
            'timestamp': time.time(),
            'last_otp_sent': time.time()
        }

        if send_email('Your OTP for Signup', [email], f'Your OTP is: {otp}'):
            flash("OTP sent to your email.", "info")
        else:
            flash("Failed to send OTP. Please try again later.", "danger")
            return redirect(url_for('recruiter_auth'))

        return redirect(url_for('verify_recru_otp'))
    elif response.strip()=='no':
        flash("Please use a valid recruiter/company email to sign up.", "danger")
        return redirect(url_for('recruiter_auth'))
    else:
        flash("Unexpected error in recruiter verification.", "danger")
        return redirect(url_for('recruiter_auth'))


@app.route('/verify_recru_otp', methods=['GET', 'POST'])
def verify_recru_otp():
    signup_data = session.get('recru_signup_data')

    if not signup_data:
        flash("Session expired. Please start signup again.", "danger")
        return redirect(url_for('recruiter_auth'))

    MAX_OTP_AGE = 300  # 5 minutes

    if request.method == 'POST':
        entered_otp = request.form['otp'].strip()

        if time.time() - signup_data.get('timestamp', 0) > MAX_OTP_AGE:
            session.pop('recru_signup_data', None)
            flash("OTP expired. Please sign up again.", "warning")
            return redirect(url_for('recruiter_auth'))

        if entered_otp == signup_data.get('otp'):
            email = signup_data['email']
            password = signup_data['password']

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO recruiter (recruiter_email, recruiter_password)
                VALUES (%s, %s)
            """, (email, password))
            mysql.connection.commit()
            cur.close()

            session.pop('recru_signup_data', None)
            flash("Signup successful. Please log in.", "success")
            return redirect(url_for('recruiter_auth'))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template('verify_recru_otp.html')

@app.route('/resend_recru_otp')
def resend_recru_otp():
    signup_data = session.get('recru_signup_data')

    if not signup_data:
        flash("Session expired. Please start signup again.", "danger")
        return redirect(url_for('recruiter_auth'))

    # Cooldown: allow resend only if 30 seconds have passed since last OTP sent
    last_sent = signup_data.get('last_otp_sent', 0)
    if time.time() - last_sent < 30:
        flash("Please wait before resending OTP again.", "warning")
        return redirect(url_for('verify_recru_otp'))

    new_otp = str(random.randint(100000, 999999))
    signup_data['otp'] = new_otp
    signup_data['timestamp'] = time.time()
    signup_data['last_otp_sent'] = time.time()
    session['recru_signup_data'] = signup_data

    if send_email('Your New OTP for Signup', [signup_data['email']], f'Your new OTP is: {new_otp}'):
        flash("A new OTP has been sent to your email.", "info")
    else:
        flash("Failed to send OTP. Please try again later.", "danger")

    return redirect(url_for('verify_recru_otp'))

@app.route('/recruiter_login', methods=['POST'])
def recruiter_login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recruiter WHERE recruiter_email = %s", (email,))
    user = cur.fetchone()#user is tuple here
    cur.close()
    if user and check_password_hash(user[2], password):
        session['user'] = email
        session['recruiter_id']=user[0]
        flash("Logged in successfully.", "success") 
        return redirect(url_for('recruiter_analyser'))
    else:
        flash("Invalid credentials", "danger")
        return redirect(url_for('recruiter_auth'))

@app.route('/forgot_recru_password', methods=['GET', 'POST'])
def forgot_recru_password():
    # Get the email from query param if exists (email typed on login)
    login_email = request.args.get('email', '').strip()

    if request.method == 'POST':
        email_entered = request.form['email'].strip()

        # Check if email entered matches login_email (if login_email provided)
        if login_email and email_entered != login_email:
            flash("Email entered does not match the email from the login page.", "danger")
            return render_template('forgot_recru_password.html', email=email_entered)

        
        cur = mysql.connection.cursor()
        cur.execute("SELECT recruiter_id FROM recruiter WHERE recruiter_email = %s", (email_entered,))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("Email not found.", "danger")
            return render_template('forgot_recru_password.html', email=email_entered)

        token = serializer.dumps(email_entered, salt='reset-password')
        link = url_for('reset_recru_password', token=token, _external=True)

        if send_email("Reset Your Password", [email_entered], f"Click the link to reset your password: {link}"):
            flash("Password reset link sent to your email.", "info")
            return redirect(url_for('recruiter_auth'))
        else:
            flash("Failed to send reset email. Please try again later.", "danger")
            return render_template('forgot_recru_password.html', email=email_entered)

    return render_template('forgot_recru_password.html', email=login_email)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_recru_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Link expired or invalid.", "danger")
        return redirect(url_for('recruiter_auth'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('reset_recru_password', token=token))

        hashed = generate_password_hash(new_password)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE recruiter SET recruiter_password = %s WHERE recruiter_email = %s", (hashed, email))
        mysql.connection.commit()
        cur.close()

        session['user'] = email
        flash("Password reset successful.", "success")
        return redirect(url_for('recruiter_auth'))

    return render_template('reset_recru_password.html')

class Resume_Analyser:
    def __init__(self,resume,job_description,groq_api_key):
        self.resume=resume
        self.job_description=job_description
        self.groq_api_key=groq_api_key  

    def extract_text_from_resume(self):
        text = ""
        with fitz.open(stream=self.resume.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    
    def extract_resume_data(self):
            llm = ChatGroq(model='gemma2-9b-it', groq_api_key=self.groq_api_key)  # Changed to valid model name if 'gemma2-9b-it' fails
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume parser. Extract the following information from the given resume text and return it as a JSON object with these keys: "
            "name, email, phone, skills (list), education (list of objects with degree, institution, start_date, end_date), "
            "work_experience (list of objects with company, role, start_date, end_date, location), and total_experience (years). "
            "If any field is missing, use null or an empty list.
            "use only the above key names like use there must present "skills" key don't use
                "required_skills" instead "skills" please."
            "store email in list"
            "Return only the JSON object. and don't give json word too in the output."""),
                ("user", "Question:{question}")
            ])
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser

            self.resume.seek(0)  # Reset pointer to the start
            resume_text = self.extract_text_from_resume()
            response = chain.invoke({
                "question": resume_text
            })
            cleaned = re.sub(r'``````', '', response).strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM response is not valid JSON: {e}"+cleaned,'error')
        
    def extract_job_desc(self):
            llm = ChatGroq(model='gemma2-9b-it', groq_api_key=self.groq_api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert job description parser. Extract the following information from the given job description text and return it as a JSON object with these keys: "
            "job_title, company, location, skills (list), responsibilities (list), qualifications (list), experience_level (e.g., Entry, Mid, Senior), "
            "education_requirements (list)."
            "If any field is missing, use null or an empty list.
            "use only the above key names.
            "Return only the JSON object."""),
                ("user", "Question:{question}")
            ])
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser

            response = chain.invoke({
                "question": self.job_description
            })
            cleaned = re.sub(r"```(?:json)?", "", response).strip("` \n")
            #cleaned['type']=f'{type(cleaned)}'
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM response is not valid JSON: {e}\nLLM Raw Output:\n{response}\nCleaned:\n{cleaned}",'error')
    def skills_information(self,resume_skills,job_skills):
            resume_score = 0
            resume_skills=[skill.lower() for skill in resume_skills]
            job_skills=[skill.lower() for skill in job_skills]
            matched_skills = []
            missing_skills = []

            for skill in job_skills:
                if skill in resume_skills:
                    resume_score += 1
                    matched_skills.append(skill)
                else:
                    missing_skills.append(skill)

            resume_score = int((resume_score / len(job_skills))*100) if job_skills else 0
            return missing_skills,matched_skills,resume_score


    def course_recommender(self,missing_skills):
            missing_skills.append('Tips for good Resume.')

            llm = ChatGroq(model='gemma2-9b-it', groq_api_key=self.groq_api_key)
            output_parser = StrOutputParser()

            prompt = ChatPromptTemplate.from_messages([
                ("system", 
                "You are an expert assistant. I will give you a list of missing skills from a resume. "
                "For each skill, return the top 3 high-quality learning resources as clickable URLs. "
                "Output only in a valid Python dictionary format, where each skill is the key and the value is a list of 3 links. "
                "Please use double quotes for keys and values in dictionary."
                "Do not include any text outside the dictionary. No explanations, no markdown, no extra formatting."
                ),
                ("user", "Missing Skills: {question}")
            ])

            chain = prompt | llm | output_parser
            response = chain.invoke({
                    "question":missing_skills
                })
            cleaned = re.sub(r'``````', '', response).strip()
            try:
                a=json.loads(cleaned)
                return a
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM response is not valid JSON: {e}"+cleaned,'error')
            

    def Job_role_Predictor(self):
            llm = ChatGroq(model='gemma2-9b-it', groq_api_key=self.groq_api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert job role predictor.Your job is to predict the most
                 suitable job role for the given resume data and ouput the job_role name.
                 you should output only the name of job and don't provide any other explanation.
                 **Remember provide only JOB ROLE NAME as output."""),
                ("user", "Question:{question}")
            ])
            output_parser = StrOutputParser()
            chain = prompt | llm | output_parser
            resume_data = self.extract_resume_data()
            response = chain.invoke({
                "question": resume_data
            })
            return response

 

@app.route('/job_seeker', methods=['GET', 'POST'])
def job_seeker():
    if 'user' not in session:
        flash("You need to log in to access this page.", "warning")
        return redirect(url_for('jobseeker_auth'))

    cursor = None
    matched_skills=[]
    missing_skills = []
    resume_score = 0
    recom_courses = {}
    js_name=''
    skills=''
    session['oper_id']=0
    if request.method == 'POST':
        try:
            if 'resume' not in request.files or 'job_description' not in request.form:
                flash('No resume or job description in request.', 'error')
                return redirect(request.url)

            resume = request.files['resume']
            job_description = request.form.get('job_description')

            if resume.filename == '' or job_description.strip() == '':
                flash('No file selected or job description is empty.', 'error')
                return redirect(request.url)
            #Ask permission to the job_seeker

            # Analyze resume
            analyser = Resume_Analyser(resume, job_description, groq_api_key)
            resume_data = analyser.extract_resume_data()
            job_data = analyser.extract_job_desc()

            resume_skills = resume_data.get('skills', [])
            job_skills = job_data.get('skills', [])

            if not isinstance(resume_skills, list) or not isinstance(job_skills, list):
                flash('Skills must be lists.', 'error')
                return redirect(request.url)

            # Skill analysis
            missing_skills, matched_skills, resume_score = analyser.skills_information(resume_skills, job_skills)
            job_role = analyser.Job_role_Predictor()
           
            js_name=resume_data.get('name', '')
            # Save resume file
            resume_path = os.path.join(UPLOAD_FOLDER, resume.filename)
            resume.seek(0)  
            resume.save(resume_path)

            contact_email = resume_data.get('email', '')
            if type(contact_email)==type([]):
                contact_email=contact_email[0]
            if len(missing_skills)!=0:
                recom_courses = analyser.course_recommender(missing_skills)
            missing_skills=missing_skills[:-1]
            session['missing_skills']=missing_skills
            session['matched_skills']=matched_skills
            session['resume_score']=resume_score
            session['recom_courses']=recom_courses
            if len(resume_skills)!=0:
                for i in range(len(resume_skills)):#To save the matched_skill in the form of string
                    skills+=resume_skills[i]+','
                skills=skills[:-1]
            cursor = mysql.connection.cursor()
            cursor.execute("""select * from js_operation where js_name=%s and resume_path=%s and
                           resume_score=%s and job_role=%s and contact_email=%s and skills=%s""",
                           (js_name,resume_path,resume_score,job_role,contact_email,skills))
            row=cursor.fetchone()
            if row!=None:
                print(row)
                session['oper_id']=row[1]
                print(session['oper_id'])
            if row==None:
                cursor.execute("""
                    insert into js_operation (js_id,js_name,resume_path,resume_score,job_role,contact_email,skills)
                            values(%s,%s,%s,%s,%s,%s,%s)""", 
                            (session.get('js_id'),js_name,resume_path, resume_score, job_role, contact_email,skills))
            
                oper_id = cursor.lastrowid#retrives the last oper_id
                session['oper_id']=oper_id
                if len(missing_skills)!=0:
                    for missing_skill in missing_skills:
                        cursor.execute("""
                                    insert ignore into missing_skills (oper_id,missing_skill) values(%s,%s)""",
                                    (oper_id,missing_skill))
                        #we can't use fetchone after the insert query.AS it has int value
                        cursor.execute("""
                                        select ms_id from missing_skills 
                                        WHERE oper_id = %s and missing_skill = %s
                                    """, (oper_id, missing_skill))
                        ms_id=cursor.fetchone()[0]
                        for course_link in recom_courses[missing_skill]:
                            cursor.execute("""
                                        insert ignore into recommended_courses (ms_id,course_link)
                                        values(%s,%s)""",
                                        (ms_id,course_link))

                mysql.connection.commit()

            flash("Resume Analysed Successfully", 'success')
            return render_template("job_seeker.html", show_results=True,
                           matched_skills=matched_skills,
                           missing_skills=missing_skills, 
                           resume_score=resume_score,
                           recom_courses=recom_courses,
                           oper_id=session['oper_id'] if session['oper_id'] != 0 else None)
        except Exception as e:
            flash( str(e),'error')
        finally:
            if cursor:
                cursor.close()
    # GET request: hide results
    return render_template("job_seeker.html",
                           show_results=False,
                           matched_skills=[],
                           missing_skills=[],
                           resume_score=0,
                           recom_courses={},
                           name='',oper_id=session['oper_id'] if session['oper_id'] != 0 else None)


@app.route('/recruiter_analyser', methods=['GET', 'POST'])
def recruiter_analyser():
    if 'user' not in session:
        flash("You need to log in to access this page.", "warning")
        return redirect(url_for('recruiter_auth'))
    cursor = None
    missing_skills = []
    matched_skills=[]
    resume_score = 0
    contact_email=''
    mat_skill_str=''
    if request.method == 'POST':
        try:
            if 'resume' not in request.files or 'job_description' not in request.form:
                flash('No resume or job description in request.', 'error')
                return redirect(request.url)

            resume = request.files['resume']
            job_description = request.form.get('job_description')

            if resume.filename == '' or job_description.strip() == '':
                flash('No file selected or job description is empty.', 'error')
                return redirect(request.url)
            #Ask permission to the job_seeker

            # Analyze resume
            analyser = Resume_Analyser(resume, job_description, groq_api_key)
            resume_data = analyser.extract_resume_data()
            job_data = analyser.extract_job_desc()
            resume_skills = resume_data.get('skills', [])
            job_skills = job_data.get('skills', [])

            if not isinstance(resume_skills, list) or not isinstance(job_skills, list):
                flash('Skills must be lists.', 'error')
                return redirect(request.url)

            # Skill analysis
            missing_skills, matched_skills, resume_score = analyser.skills_information(resume_skills, job_skills)
            job_role = analyser.Job_role_Predictor()
           
            contact_email = resume_data.get('email', '')
            if type(contact_email)==type([]):
                contact_email=contact_email[0]

            candidate_name = resume_data.get('name', '')

            
            if len(matched_skills)!=0:
                for i in range(len(matched_skills)):#To save the matched_skill in the form of string
                    mat_skill_str+=matched_skills[i]+','
                mat_skill_str=mat_skill_str[:-1]
                

            # Save resume file
            resume_path = os.path.join(UPLOAD_FOLDER, resume.filename)
            resume.seek(0)  
            resume.save(resume_path)
    
            # Update database
            cursor = mysql.connection.cursor()
            cursor.execute("""select * from recruiter_uploads where recruiter_id=%s and
                           candidate_name=%s and resume_path=%s and resume_score=%s and job_role=%s and
                           contact_email=%s and mat_skill_str=%s""",
                           (session.get('recruiter_id'), candidate_name, resume_path, resume_score, job_role, contact_email,mat_skill_str))
            row=cursor.fetchone()
            if row==None:
                cursor.execute("""
                    INSERT INTO recruiter_uploads(
                        recruiter_id, candidate_name, resume_path, resume_score, job_role, contact_email,mat_skill_str
                    )
                    VALUES (%s, %s, %s, %s, %s, %s,%s)
                """, (session.get('recruiter_id'), candidate_name, resume_path, resume_score, job_role, contact_email,mat_skill_str))
                
                mysql.connection.commit()

            flash("Resume Analysed Successfully", 'success')
            return render_template("recruiter_analyser.html", 
                            show_results=True,
                            missing_skills=missing_skills,
                            resume_score=resume_score,
                            matched_skills=matched_skills,
                            contact_email=contact_email,
                            mat_skill_str=mat_skill_str)
        except Exception as e:
            flash( str(e),'error')
        finally:
            if cursor:
                cursor.close()
    # GET request
    return render_template("recruiter_analyser.html",
                           show_results=False,
                           missing_skills=[],
                           resume_score=0,
                           matched_skills=[],
                           contact_email='',
                           mat_skill_str='')


@app.route('/js_view_uploads', methods=['GET', 'POST'])
def js_view_uploads():
    if 'user' not in session:
        flash("You need to log in to access this page.", "warning")
        return redirect(url_for('jobseeker_auth'))
    cursor = mysql.connection.cursor()

    js_id = session.get('js_id')
    search_query = request.form.get('search', '').strip()  # For GET requests with query param
    # Base query
    base_query = """
        SELECT oper_id,job_role, resume_path, resume_score, skills
        FROM js_operation
        WHERE js_id = %s
    """
    params = [js_id]

    # Modify query if searching
    if search_query:
        base_query += " AND ( job_role LIKE %s)"
        like_query = f"%{search_query}%"
        params.extend([like_query])

    cursor.execute(base_query, tuple(params))
    results = cursor.fetchall()

    uploads = []
    for row in results:
        oper_id=row[0]
        cursor.execute("select missing_skill from missing_skills where oper_id=%s",
                       (oper_id,))
        missing_skills=cursor.fetchall()
        uploads.append({
            'jobrole': row[1],
            'filename': os.path.basename(row[2]),
            'score': row[3],
            'skills': [skill.strip() for skill in row[4].split(',')] if row[4] else ['No Matching Skills'],
            'missing_skills':[ms[0] for ms in missing_skills] if missing_skills else ['Great No Missing Skills']
        })

    cursor.close()
    return render_template('js_view_uploads.html', uploads=uploads, search_query=search_query)


@app.route('/view_uploads', methods=['GET', 'POST'])
def view_uploads():
    if 'user' not in session:
        flash("You need to log in to access this page.", "warning")
        return redirect(url_for('recruiter_auth'))
    cursor = mysql.connection.cursor()

    recruiter_id = session.get('recruiter_id')
    search_query = request.form.get('search', '').strip()  # For GET requests with query param
    # Base query
    base_query = """
        SELECT candidate_name, contact_email, job_role, resume_path, resume_score, mat_skill_str
        FROM recruiter_uploads
        WHERE recruiter_id = %s
    """
    params = [recruiter_id]

    # Modify query if searching
    if search_query:
        base_query += " AND (candidate_name LIKE %s OR job_role LIKE %s)"
        like_query = f"%{search_query}%"
        params.extend([like_query, like_query])

    cursor.execute(base_query, tuple(params))
    results = cursor.fetchall()

    uploads = []
    for row in results:
        uploads.append({
            'name': row[0],
            'email': row[1],
            'jobrole': row[2],
            'filename': os.path.basename(row[3]),
            'score': row[4],
            'skills': [skill.strip() for skill in row[5].split(',')] if row[5] else ['No Matching Skills']
        })

    cursor.close()
    return render_template('view_uploads.html', uploads=uploads, search_query=search_query)

@app.route('/show_js_to_recru',methods=['GET','POST'])
def show_js_to_recru():
    if 'user' not in session:
        flash("You need to log in to access this page.", "warning")
        return redirect(url_for('recruiter_auth'))
    cursor = mysql.connection.cursor()

    search_query = request.form.get('search', '').strip()  # For GET requests with query param
    # Base query
    base_query = """
        SELECT js_name, contact_email, job_role, resume_path, resume_score, skills
        FROM js_operation
        WHERE permission=1
    """
    
    params=[]
    # Modify query if searching
    if search_query:
        base_query += " AND (js_name LIKE %s OR job_role LIKE %s)"
        like_query = f"%{search_query}%"
        params.extend([like_query, like_query])

    cursor.execute(base_query, tuple(params))
    results = cursor.fetchall()

    uploads = []
    for row in results:
        uploads.append({
            'name': row[0],
            'email': row[1],
            'jobrole': row[2],
            'filename': os.path.basename(row[3]),
            'score': row[4],
            'skills': [skill.strip() for skill in row[5].split(',')] if row[5] else ['No Matching Skills']
        })

    cursor.close()
    return render_template('show_js_to_recru.html', uploads=uploads, search_query=search_query)


@app.route('/uploads/<path:filename>')
def serve_resume(filename):
    uploads_dir = os.path.join(app.root_path, 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/share_resume', methods=['POST'])
def share_resume():
    consent = request.form.get('consent')
    oper_id = oper_id = request.form.get('oper_id') or session.get('oper_id')
    if not consent or not oper_id:
        flash("Missing consent or operation ID.", "error")
        return redirect(url_for('job_seeker'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE js_operation SET permission = %s WHERE oper_id = %s
        """, (consent == 'yes', oper_id))
        mysql.connection.commit()
        cursor.close()
        if consent=='yes':     
            flash("You have accepted.Thank you for the response.", "success")
        elif consent=='no':
            flash("You haven't accepted.Thank you for the response.", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")

    return render_template("job_seeker.html", show_results=True,
                           matched_skills=session['matched_skills'],
                           missing_skills=session['missing_skills'], 
                           resume_score=session['resume_score'],
                           recom_courses=session['recom_courses'],
                           oper_id=session.get('oper_id')if oper_id!= 0 else None)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))

"""Todo:0.take permission from the job_seeker and store it in db.
        1.logout for job_seeker (completed)       
        2.take his/her name and greet the person at the top with their name.
        3.showing the history of the person.(completed)
        4.Recruiter login authentucation.(completed)
        5.Recruiter resume_analyser.(completed)
        6.Showing the recruiter the persons when he/she search for a perticular job role(completed)
        7.showing the history to the recruiter.(completed)
        8.Testing and Deploying."""
"""Problems:
        1.In recruiter only company mails should be allowed.(no need at present)
        2.In recruiter Analyser the below sections should be visible only after results is analysed.(jayanthi)
        3.Some times llm errors are occuring.
        4.Redundant entries shouldn't be allowed into database(if present take best results only).(completed)
        5.After clicking permission button the resume analyser is becoming empty.(completed)
        6.Show some good technical names in website.(completed)
        7.Show the pop up messages properly.(jayanthi)
        8.find a good llm model
        """


if __name__ == '__main__':
    app.run(debug=True)
