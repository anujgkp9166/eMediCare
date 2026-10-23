# eMediCare+  ·  Healthcare, Just a Click Away

A Django website that connects **appointment → doctor consultation → diagnostic test (home sample collection) → digital report → follow-up** on one platform.
Theme and logo follow the eMediCare+ brand (navy blue, green, red).

## Who controls what

| Role | What they can do |
|------|------------------|
| **Admin** (superuser) | Controls everything from `/admin/`: users, doctors & their time slots, appointments (confirm / complete / cancel, add video link, doctor advice), labs, test catalogue & prices, test requests (schedule / collect), report upload, feedback. Dashboard shows pending work at a glance. |
| **Patient** | Registers themselves, books appointments, requests tests, views own reports, books follow-ups. |
| **Doctor** | Registers at `/accounts/register/doctor/` (speciality, registration number, fee, days and sessions), then logs in to see their own schedule (read-only). **Hidden from patients until admin verifies.** |
| **Lab partner** | Registers at `/accounts/register/lab/` (lab details, licence number, home collection), then logs in to see requests for their lab (read-only). **Hidden from patients until admin verifies.** Admin then sets up the lab's test price list. |

Admin approval flow: **Admin → Doctors (or Labs) → filter “Is verified: No”**, check the registration/licence number, tick *Verified* (or use the bulk action). The admin dashboard shows the number of doctors and labs awaiting approval. Admin can also add doctors and labs directly without any login.

## Run on your computer

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations accounts care diagnostics core
python manage.py migrate
python manage.py createsuperuser   # this is your admin login
python manage.py seed_data         # 8 doctors, 5 nearby labs, 15 tests with prices (edit/replace in admin)
python manage.py runserver
```

Open http://127.0.0.1:8000/ and the admin at http://127.0.0.1:8000/admin/

Want ready-made logins and sample activity? Run
`python manage.py seed_data --sample-accounts "ChooseAPassword"` to create `patient1` (with appointments, a test and a report), `doctor1`, `lab1`, plus `doctor2` and `lab2` that are waiting for approval.
**Delete these accounts from the admin before the site goes public.**

> Run `makemigrations` once and commit the generated `migrations/` folders to GitHub. After that, deployment only needs `migrate`.

## Add real content (Admin → Control Centre)

1. **Doctors**: add name, speciality, fee, photo, weekly time slots (inline table). Tick *Verified* to show on the site.
2. **Labs**: add lab details, then its price list (which tests, price, report time). Tick *Verified*.
3. **Tests**: the master list of test names/categories.
4. **Appointments / Test requests**: use the list actions (Confirm, Mark completed, Schedule, Mark collected). Upload the report inside the test request (Report section). The status becomes *Report ready* automatically.

## Deploy (Render / Railway / Replit / PythonAnywhere)

- Build command: `./build.sh` (installs, migrates and loads the starting data)  ·  Start command: `gunicorn config.wsgi`
- Set the environment variables from `.env.example` (`DEBUG=0` and a long random `SECRET_KEY` are required).
- Generate a key: `python -c "import secrets;print(secrets.token_urlsafe(50))"`

**Important about storage:** the default SQLite database and uploaded files (doctor photos, patient reports) live on the server's disk. Many free hosts wipe the disk on redeploy. For a real launch use a persistent disk (set `SQLITE_PATH`, `MEDIA_ROOT`, `PRIVATE_MEDIA_ROOT` to that disk) or move to PostgreSQL and cloud storage.

## Logo & colours

Logo files are in `static/img/`. All colours are variables at the top of `static/css/site.css` (and `static/css/admin.css` for the admin panel).

## Project layout

```
config/        settings, urls
accounts/      custom User (patient/doctor/lab/admin), login, register, profile
care/          doctors, time slots, appointments, booking, doctor portal
diagnostics/   labs, tests, price list, test requests, private reports, lab portal
core/          home/about/contact, patient dashboard, feedback, branded admin site, seed_data
templates/  static/
```

## Safety notes

- The site does not diagnose. Disclaimers appear on key pages; keep them.
- Patient reports are stored outside the public media folder and served only to the patient, the lab owner and staff.
- Seed doctors/labs/prices are **placeholders**. Replace them with real partner details before real use.
