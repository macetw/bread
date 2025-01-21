#!/usr/bin/env python3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import parser
import re
import pytz
from datetime import datetime
import json
from pathlib import Path

TARGET_TIMEZONE = "America/Los_Angeles"
SPREADSHEET_ID = '1nt4d7X79caoTojtzoqSnHXwTUUkF1ftnz9nB5aetLMk'
RANGE = 'Sheet1'
TRANSLATION = "NIV"
PATTERN = re.compile(r"^(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)*)(?:\s(\d+))(?::(\d+)(?:-(\d+))?)?$")
BOOK_ABBREVIATIONS = {
    "Genesis": "GEN",
    "Exodus": "EXO",
    "Leviticus": "LEV",
    "Numbers": "NUM",
    "Deuteronomy": "DEU",
    "Joshua": "JOS",
    "Judges": "JUD",
    "Ruth": "RUT",
    "1 Samuel": "1SA",
    "2 Samuel": "2SA",
    "1 Kings": "1KI",
    "2 Kings": "2KI",
    "1 Chronicles": "1CH",
    "2 Chronicles": "2CH",
    "Ezra": "EZR",
    "Nehemiah": "NEH",
    "Esther": "EST",
    "Job": "JOB",
    "Psalm": "PSA",
    "Psalms": "PSA",
    "Proverbs": "PRO",
    "Ecclesiastes": "ECC",
    "Song of Solomon": "SOS",
    "Isaiah": "ISA",
    "Jeremiah": "JER",
    "Lamentations": "LAM",
    "Ezekiel": "EZE",
    "Daniel": "DAN",
    "Hosea": "HOS",
    "Joel": "JOE",
    "Amos": "AMO",
    "Obadiah": "OBA",
    "Jonah": "JON",
    "Micah": "MIC",
    "Nahum": "NAH",
    "Habakkuk": "HAB",
    "Zephaniah": "ZEP",
    "Haggai": "HAG",
    "Zechariah": "ZEC",
    "Malachi": "MAL",
    "Matthew": "MAT",
    "Mark": "MAR",
    "Luke": "LUK",
    "John": "JOH",
    "Acts": "ACT",
    "Romans": "ROM",
    "1 Corinthians": "1CO",
    "2 Corinthians": "2CO",
    "Galatians": "GAL",
    "Ephesians": "EPH",
    "Philippians": "PHP",
    "Colossians": "COL",
    "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH",
    "1 Timothy": "1TI",
    "2 Timothy": "2TI",
    "Titus": "TIT",
    "Philemon": "PHI",
    "Hebrews": "HEB",
    "James": "JAM",
    "1 Peter": "1PE",
    "2 Peter": "2PE",
    "1 John": "1JN",
    "2 John": "2JN",
    "3 John": "3JN",
    "Jude": "JUD",
    "Revelation": "REV"
}

timezone = pytz.timezone(TARGET_TIMEZONE)
today = datetime.now(pytz.utc).astimezone(timezone)

# Authenticate with a service account
creds = service_account.Credentials.from_service_account_file(
    'secret.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)

# Initialize the Google Drive API
service = build('sheets', 'v4', credentials=creds)

# Retrieve the document metadata
#file = service.files().get(fileId=SPREADSHEET_ID, fields='name, webViewLink').execute()
#print(f"Document Name: {file['name']}")
#print(f"Web View Link: {file['webViewLink']}")

sheet = service.spreadsheets()

# Fetch the data
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()

# Extract the values
values = result.get('values', [])

# Print the retrieved data
if not values:
    print("No data found.")
    exit()

title = ""
data = dict()
line = -1
for row in values:
    line += 1
    if len(row) < 2:
        print(f"no data on row {line}.")
        continue
    # print(row)  # Each row is a list representing a row of the spreadsheet
    day = parser.parse(row[0]).date()
    matches = re.search(PATTERN, row[1])
    if not matches:
        print(f"row {row} pattern mismatch")
        continue
    book = matches[1]
    chapter = matches[2]
    verse = matches[3]
    verse_end = matches[4]
    # print(f"book {book}   chapter {chapter}     verse {verse}   verse-end {verse_end}")
    if book not in BOOK_ABBREVIATIONS:
        print(f"row {row} is invalid")
        continue
    book_abbreviation = BOOK_ABBREVIATIONS[book]
    if len(row) > 2 and row[2]:
        title = row[2]

    youversion_url = f"https://www.bible.com/bible/111/{book_abbreviation}.{chapter}"
    if verse:
        youversion_url += f".{verse}"
        if verse_end:
            youversion_url += f"-{verse_end}"
    if str(day) not in data:
        data[str(day)] = []
    data[str(day)].append((youversion_url,row[1],title))

urlfile = Path("/var/www/bread_app/urls.json")
with urlfile.open("w", encoding="utf-8") as file:
    json.dump(data, file)
