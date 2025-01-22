from flask import Flask, render_template, session, redirect, url_for, request
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import pytz

TEMPLATE_PATH="/var/www/bread_app/templates"
STATIC_PATH="/var/www/bread_app/static"
TARGET_TIMEZONE="America/Los_Angeles"

app = Flask(__name__, template_folder=TEMPLATE_PATH, static_folder=STATIC_PATH)
app.config["TEMPLATES_AUTO_RELOAD"] = False
app.config["SESSION_COOKIE_SAMESITE"] = 'None'
app.config["SESSION_COOKIE_SECURE"] = True
app.secret_key = 'XCYD74SACIEAQtOuHZL4tqNT5KEmWAFL'
app.permanent_session_lifetime = timedelta(minutes=30)

class DataHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.data = dict()

    def read_data(self):
        urls = Path("bread_app/urls.json")
        with urls.open("r") as file:
            self.data = json.load(file)

    def get_data(self, key: str) -> list[str, str, str]:
        if not self.data:
            self.read_data()
        if key in self.data:
            return self.data[key]
        return []

    def get_all_data(self) -> list[str, str, str]:
        if not self.data:
            self.read_data()
        return_value = []
        for key, datum in self.data.items():
            return_value.extend(datum)
        return return_value

    def data_exists(self, key: str) -> bool:
        if not self.data:
            self.read_data()
        return key in self.data

    def raw_data(self) -> str:
        return json.dumps(self.data)

data_handler = DataHandler()


@app.route("/")
def home() -> str:
    session.permanent = True
    if 'day_offset' not in session:
        session['day_offset'] = 0
    day_offset = session['day_offset']
    data = info(day_offset=day_offset)
    yesterday_exists = does_offset_exist(day_offset-1)
    tomorrow_exists = does_offset_exist(day_offset+1)
    if data:
        return render_template(
          "bread.html",
          is_today=(day_offset == 0),
          yesterday_exists=yesterday_exists,
          tomorrow_exists=tomorrow_exists,
          title=data[0][2],
          data=data,
          offset_description=offset_description(day_offset),
        )
    else:
        foo = todaystr(day_offset=day_offset)
        return f"There's no data for {foo} for offset {day_offset}"

@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    if request.method == "GET":
        return render_template("enroll.html")
    else:
        phone = request.form.get('phone')
        return(f"Sounds like you wanna enroll for {phone}")

@app.route("/reread")
def reread():
    data_handler.read_data()
    return home()

@app.route('/test')
def test() -> str:
    data = data_handler.get_all_data()
    if data:
        return render_template(
          "bread.html",
          is_today=True,
          yesterday_exists=False,
          tomorrow_exists=False,
          title="Test Data",
          data=data,
          offset_description="",
        )
    else:
        return f"There's no data."

@app.route('/today')
def today():
    session.clear()
    return redirect(url_for('home'))

@app.route('/increase_day')
def increase_day() -> str:
    new_offset = session.get('day_offset', 0) + 1
    session['day_offset'] = new_offset
    return redirect(url_for('home'))

@app.route('/decrease_day')
def decrease_day() -> str:
    new_offset = session.get('day_offset', 0) - 1
    session['day_offset'] = new_offset
    return redirect(url_for('home'))

def offset_description(day_offset: int) -> str:
    if day_offset == 0:
        return ""
    elif day_offset == 1:
        return "Tomorrow"
    elif day_offset == 2:
        return "Day after tomorrow"
    elif day_offset >= 3 and day_offset < 7:
        return day_of_offset(day_offset).strftime('%A')
    elif day_offset == -1:
        return "Yesterday"
    elif day_offset == -2:
        return "Day before yesterday"
    elif day_offset <= -3 and day_offset > -7:
        return "Last " + day_of_offset(day_offset).strftime('%A')
    else:
        return day_of_offset(day_offset).strftime('%B %e')

def day_of_offset(day_offset: int) -> date:
    timezone = pytz.timezone(TARGET_TIMEZONE)
    now = datetime.now(pytz.utc).astimezone(timezone)
    return (now + timedelta(days=day_offset)).date()

def todaystr(day_offset: int=0) -> str:
    today = day_of_offset(day_offset)
    return str(today)

def info(day_offset: int=0) -> list[str, str, str]:
    key = todaystr(day_offset=day_offset)
    return data_handler.get_data(key)

def does_offset_exist(day_offset: int) -> bool:
    return data_handler.data_exists(todaystr(day_offset=day_offset))
