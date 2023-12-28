import json

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
import random
import requests
from flask_bootstrap import Bootstrap
from sqlalchemy import select, ForeignKey, Integer, desc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from flask_wtf.csrf import CSRFProtect
import re

app = Flask(__name__)

Thoughts = ["Daily Reflections: Your Personal Diary with AI Insights",
            "Capturing Moments: Share Your Day, Unlock Wisdom", "Discover Your Day: Write, Reflect, Grow",
            "My Day, My Journey: Insights with AI Companionship",
            "Journaling with Purpose: Uncover the Story of Your Day", "Embrace Each Day: Your AI-Powered Diary",
            "Your Daily Chronicle: Reflect, Record, Reimagine", "AI Diaries: Where Your Day's Tale Begins",
            "Diary of Discovery: Unveil the Essence of Your Day", "Your Personal Daybook: Craft, Reflect, Evolve"]
RANDOM_QUESTIONS = ["What were the highlights of your day?", "Were there any challenges or obstacles you faced today?",
                    "Did you learn something new today?", "How did you feel today, and why?",
                    "Is there something specific you want to remember about today?",
                    "What are your plans or goals for tomorrow?", "What was your biggest achievement today?",
                    "Did you face any unexpected surprises today?",
                    "Did you take any steps toward achieving your long-term goals today?",
                    "Did you have any meaningful interactions with friends or family today?",
                    "What's one thing you're grateful for today?",
                    "Did you experience any personal growth or self-discovery today?"]

Bootstrap(app)

app.config['SECRET_KEY'] = "youandme90through2to1forme20"

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ai-notebook-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)
# CONFIGURE TABLES
YOU_LIST = []

QUESTIONS = random.sample(RANDOM_QUESTIONS, 3)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # One-to-Many relationship with AiNotes
    notes = db.relationship("AiNotes", back_populates="author")
    goals = db.relationship("MonthlyGoal", back_populates="author")


class AiNotes(db.Model):
    __tablename__ = "ai_notes"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    img_url = db.Column(db.String(400), nullable=False)
    data = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    short_summary = db.Column(db.Text, nullable=False)
    questions = db.Column(db.Text, nullable=False)
    # Many-to-One relationship with User
    author = db.relationship("User", back_populates="notes")


class MonthlyGoal(db.Model):
    __tablename__ = "monthly_goal"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    goals = db.Column(db.String(300), nullable=False)

    # Many to one
    author = db.relationship("User", back_populates="goals")


with app.app_context():
    db.create_all()

# Configure Flask-login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_required
@app.route("/home")
def home():
    random_thoughts = random.choice(Thoughts)
    user_id = current_user.id

    # Query the last five notes by ordering them by date in descending order and limiting the result to 5
    notes = AiNotes.query.filter_by(author_id=user_id).order_by(desc(AiNotes.date)).limit(6).all()

    # Query for checking user has there monthly goal or not
    goal = MonthlyGoal.query.filter_by(author_id=user_id).order_by(desc(MonthlyGoal.date)).limit(1).first()

    if goal is None:
        goal = False
    else:
        data = json.loads(goal.goals)
        return render_template('index.html', thought=random_thoughts, goals=goal, data=data,
                               questions=QUESTIONS,
                               all_notes=notes, current_user=current_user)

    return render_template('index.html', thought=random_thoughts, goals=goal, questions=QUESTIONS,
                           all_notes=notes, current_user=current_user)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = request.form
        email = form.get('email')
        password = form.get('password')

        user = User.query.filter_by(email=email).first()
        if user is None:
            flash("That email does not exist, please try again.")
        elif user is not None and check_password_hash(user.password, password):
            login_user(user)
            user_id = current_user.id

            # Query the last five notes by ordering them by date in descending order and limiting the result to 5
            notes = AiNotes.query.filter_by(author_id=user_id).order_by(desc(AiNotes.date)).limit(6).all()
            random_thoughts = random.choice(Thoughts)

            goal = MonthlyGoal.query.filter_by(author_id=user_id).order_by(desc(MonthlyGoal.date)).limit(1).first()

            if goal is None:
                goal = False
            else:
                data = json.loads(goal.goals)
                return render_template('index.html', thought=random_thoughts, goals=goal, data=data,
                                       questions=QUESTIONS,
                                       all_notes=notes, current_user=current_user)

            return render_template('index.html', thought=random_thoughts, goals=goal, questions=QUESTIONS,
                                   all_notes=notes, current_user=current_user)

        else:
            flash("Password is incorrect, please try again.")
    return render_template('login.html', current_user=current_user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        form = request.form
        user = User.query.filter_by(email=form.get('email')).first()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        else:
            hash_and_salted_password = generate_password_hash(
                form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                email=form.get('email'),
                name=form.get('name'),
                password=hash_and_salted_password,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))

    return render_template('signup.html', current_user=current_user)


@app.route("/add-new-note", methods=['POST'])
def add_new_note():
    global data_dict
    if request.method == "POST":
        # get data from form
        data = request.form.to_dict()

        # url of A.I. tool
        url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key=AIzaSyDPgRBC5cQd7eJ7Pi75-nvzyLI86fzaano"

        questions = {
            "How was your day overall?": data['response1'],
            QUESTIONS[0]: data['response2'],
            QUESTIONS[1]: data['response3'],
            QUESTIONS[2]: data['response4'],
        }

        payload = {
            "prompt": {
                "text": f"Analysis {questions} data, by review the user's daily reflections and provide a concise title and summary for each entry. The summary should include key points, suggestions, and an overall summary of the day based on their reflections. Create a dictionary that contains only titles and summaries of this."
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            new_data = response.json()
            #  here get data dictionary and get output key from data dictionary
            new = new_data['candidates'][0]['output']

            # split new line
            lines = new.split('\n')
            print(lines)
            # now create new dictionary and list
            cleaned_list = []

            for item in lines:
                cleaned_item = item.replace('**', '').replace('*', '')
                cleaned_list.append(cleaned_item)

            # print(cleaned_list)

            data_dict = {}
            current_key = None

            for item in cleaned_list:
                if item:
                    if ':' in item:
                        current_key = item.split(':', 1)[0]
                        data_dict[current_key] = ''
                    else:
                        if current_key:
                            data_dict[current_key] += item

            # get Summary from list
            for i in cleaned_list:
                if 'Summary' in i:
                    summary = i

            # delete summary and title form dictionary because it's nun
            # del data_dict['Title']
            # del data_dict['Summary']
            summary_data = json.dumps(data_dict)

            if data_dict is {} or None:
                summary_data = json.dumps(data_dict)

            print(data_dict)
            print(cleaned_list)
        else:
            pprint.pprint(response.status_code)

        questions_list = ["How was your day overall?", QUESTIONS[0], QUESTIONS[1], QUESTIONS[2]]
        questions_json = json.dumps(questions_list)
        data_json = json.dumps(data)
        response = requests.get(
            'https://api.unsplash.com/photos/random/?client_id=ekudPmYouAOqvrVxsvim-MD-I6NqTqKHjX15qfs0YXo&query=nature aesthetic')
        res_data = response.json()
        current_datetime = datetime.now()
        img = res_data['urls']['full']
        new_note = AiNotes(
            title=cleaned_list[0],
            date=current_datetime,
            img_url=img,
            author=current_user,
            data=data_json,
            summary=summary_data,
            short_summary='pass',
            questions=questions_json
        )
        db.session.add(new_note)
        db.session.commit()
        return render_template('generic.html', current_user=current_user, data=data, date=current_datetime, img=img,
                               summry=data_dict, title=cleaned_list[0], questions=questions_list)
    return redirect(url_for('home'))


@app.route("/home/goal", methods=["GET", "POST"])
def goal_form():
    if request.method == "POST":  # Check if the request method is POST
        data = request.form.to_dict()
        data_json = json.dumps(data)
        current_datetime = datetime.now()
        new_goal = MonthlyGoal(
            date=current_datetime,
            goals=data_json,
            author=current_user
        )
        db.session.add(new_goal)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("form_top_month.html", current_user=current_user)


@app.route("/landing")
def landing():
    user_id = current_user.id  # Assuming current_user.email contains the user's ID
    notes = db.session.query(AiNotes).filter_by(author_id=user_id).order_by(desc(AiNotes.date)).all()
    # notes = db.session.query(AiNotes).get(user_id)
    return render_template("landing.html", all_notes=notes, current_user=current_user)


@app.route("/note/<int:note_id>", methods=["GET", "POST"])
def show_note(note_id):
    request_note = db.session.query(AiNotes).get(note_id)
    data = json.loads(request_note.data)
    summary = json.loads(request_note.summary)
    que = json.loads(request_note.questions)
    return render_template("single note.html", data=data, que=que, note=request_note, current_user=current_user, summary=summary)


@app.route("/delete/<int:note_id>", methods=["GET", "POST"])
def delete(note_id):
    note_to_delete = AiNotes.query.get(note_id)
    db.session.delete(note_to_delete)
    db.session.commit()
    return redirect(url_for('landing'))


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, host="localhost", port=5000)
