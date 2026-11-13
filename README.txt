SCHOLARSHIP FINDER - STARTER WEBSITE

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:
       python -m pip install -r requirements.txt
5. Run:
       python app.py
6. Open:
       http://127.0.0.1:5000/

PROJECT FEATURES
- Home page with scholarship search
- Student registration and sign-in
- Password hashing (passwords are not stored as plain text)
- SQLite student database (students.db is created automatically)
- Optional profile photo upload
- Student profile form
- Student dashboard with basic audience-based suggestions
- Logout

IMPORTANT
- Scholarship cards are starter/demo listings, not a verified live database.
  Check current eligibility, award amounts, deadlines and application links
  on each official portal before applying.
- The "Sign in with Google" option is not connected in this starter.
  Real Google OAuth needs a Google Cloud project, OAuth client credentials,
  HTTPS configuration and secure deployment.
- This is a local learning prototype, not production-ready. Before public launch,
  add CSRF protection, email verification, password reset, rate limiting,
  stronger upload validation, HTTPS, backups, privacy policy and security review.
- Change SECRET_KEY using an environment variable before deployment.
- Do not upload real sensitive student documents to this demo.
