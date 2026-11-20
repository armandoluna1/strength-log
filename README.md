# Strength Log

An original full-stack practice project for tracking strength workouts. Log a set, edit or delete it, and filter the journal by training date. The journal shows volume in pounds for the visible sets. Three sets of ten reps at 50 lb each contribute 1,500 lb.

## Run on a Mac

Install Python 3.9 or newer. Extract the project, open its folder in Terminal, and run:

```bash
python3 app.py
```

Open http://127.0.0.1:8000 in your browser. Press Control+C in Terminal to stop. No package installation or API key is required. Try entering Bench press, 8 reps, and 95 lb. Save the set, reload the page, and check that your 760 lb of volume is still there.

## How the pieces fit together

- **Browser:** Files in `web/` handle the form, history, date filter, and volume calculation.
- **Server:** `app.py` serves the interface, validates each submission, and handles HTTP requests using Python's standard library.
- **Database:** SQLite stores each set's ID, date, exercise, reps, and weight. The server creates `strength.sqlite3` on first use. The journal is shared across browser tabs using that server.

| Action | Method | Path |
| --- | --- | --- |
| List sets, newest date first | GET | /api/sets |
| Log a set | POST | /api/sets |
| Edit a set | PUT | /api/sets/{id} |
| Delete a set | DELETE | /api/sets/{id} |

POST and PUT accept a JSON body such as `{"day":"2026-11-20","exercise":"Bench press","reps":8,"weight":95}`. Enter zero weight for a bodyweight exercise. Volume counts the external weight entered.

## Upload to GitHub

Create a repository called strength-log. Select **uploading an existing file** or **Add file → Upload files**. Upload app.py, README.md, and the entire web folder, keeping its folder structure. Include .gitignore if using Git. Leave the generated database on your computer. Click **Commit changes**.

Anyone who downloads the repository can run it locally with Python. GitHub Pages hosts static files only. Running this single-user server locally keeps the journal on your computer.
