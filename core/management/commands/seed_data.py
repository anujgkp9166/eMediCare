import io
from datetime import time, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from care.models import Appointment, Doctor, DoctorSlot
from diagnostics.models import Lab, LabTest, Report, Test, TestRequest

# name, category, description, preparation
TESTS = [
    ("Complete Blood Count", "Blood test", "Checks overall blood health.", ""),
    ("Haemoglobin", "Blood test", "Measures the oxygen-carrying protein in blood.", ""),
    ("ESR", "Blood test", "A general marker of inflammation.", ""),
    ("Blood Group & Rh", "Blood test", "Determines your blood group.", ""),
    ("HbA1c", "Diabetes screening", "Average blood sugar over about 3 months.", "No fasting needed"),
    ("Fasting Blood Sugar", "Diabetes screening", "Blood sugar after fasting.", "8–10 hours fasting"),
    ("Lipid Profile", "Heart health", "Cholesterol and related fats.", "9–12 hours fasting"),
    ("Liver Function Test", "Blood test", "Checks how the liver is working.", "8 hours fasting"),
    ("Kidney Function Test", "Blood test", "Checks how the kidneys are working.", "No fasting needed"),
    ("Thyroid (TSH)", "Hormone test", "Thyroid stimulating hormone level.", "No fasting needed"),
    ("Vitamin D", "Wellness", "25-OH Vitamin D level.", "No fasting needed"),
    ("Urine Routine", "Urine test", "Basic urine examination.", "Use the sterile container provided"),
    ("Dengue NS1 Antigen", "Fever panel", "Early detection of dengue infection.", ""),
    ("Malaria Antigen", "Fever panel", "Rapid test for malaria parasite.", ""),
    ("Widal Test", "Fever panel", "Test commonly used for typhoid fever.", ""),
]

# name, area, address, phone, distance_km, home_collection, hours, {test: (price, report_hours)}
LABS = [
    ("Maharajganj Diagnostic Centre", "Civil Lines", "Civil Lines, Maharajganj", "9415000101", "1.2", True, "7:00 AM – 8:00 PM",
     {"Complete Blood Count": (450, 12), "HbA1c": (650, 24), "Thyroid (TSH)": (400, 24), "Fasting Blood Sugar": (120, 6),
      "Kidney Function Test": (600, 24), "Urine Routine": (100, 6), "Haemoglobin": (120, 6), "Dengue NS1 Antigen": (700, 12)}),
    ("CityCare Pathology", "Shastri Nagar", "Shastri Nagar, Maharajganj", "9415000102", "2.8", True, "7:30 AM – 7:30 PM",
     {"Lipid Profile": (800, 24), "Liver Function Test": (700, 24), "Vitamin D": (900, 36), "Complete Blood Count": (480, 24),
      "ESR": (120, 6), "Widal Test": (250, 12), "Malaria Antigen": (350, 6)}),
    ("Arogya Pathology & Imaging", "Station Road", "Station Road, Maharajganj", "9415000103", "1.9", True, "7:00 AM – 9:00 PM",
     {"Complete Blood Count": (420, 12), "HbA1c": (600, 24), "Lipid Profile": (750, 24), "Thyroid (TSH)": (380, 24),
      "Blood Group & Rh": (150, 4), "Urine Routine": (90, 6), "Fasting Blood Sugar": (100, 6)}),
    ("Sanjeevani Lab", "Gorakhpur Road", "Gorakhpur Road, Maharajganj", "9415000104", "3.4", True, "8:00 AM – 6:00 PM",
     {"Vitamin D": (850, 36), "Thyroid (TSH)": (420, 24), "Kidney Function Test": (580, 24), "Liver Function Test": (680, 24),
      "Dengue NS1 Antigen": (650, 12), "Widal Test": (230, 12)}),
    ("Trusted Care Diagnostics", "Nichlaul Road", "Nichlaul Road, Maharajganj", "9415000105", "4.6", False, "8:00 AM – 5:00 PM",
     {"Complete Blood Count": (400, 24), "HbA1c": (580, 36), "Lipid Profile": (700, 36), "Haemoglobin": (100, 6), "ESR": (100, 6)}),
]

# name, speciality, qualification, clinic, years, fee, languages, days, sessions
MORN, AFT = [time(10, 0), time(10, 30), time(11, 0), time(11, 30)], [time(14, 0), time(14, 30), time(15, 0), time(15, 30)]
DOCTORS = [
    ("Kavita Shukla", "General Physician", "MBBS, MD (Medicine)", "District clinic, Civil Lines", 12, 300, "Hindi, English", range(6), MORN + AFT),
    ("Rohit Verma", "Paediatrician", "MBBS, MD (Paediatrics)", "Child care clinic, Station Road", 9, 400, "Hindi, English", range(6), MORN + AFT),
    ("Sunita Mishra", "Gynaecologist", "MBBS, MS (Obs & Gynae)", "Women's care centre, Shastri Nagar", 14, 500, "Hindi, English", range(5), MORN + AFT),
    ("Amit Srivastava", "Dermatologist", "MBBS, MD (Dermatology)", "Skin & care clinic, Tehsil Road", 8, 450, "Hindi, English", range(6), AFT),
    ("Pankaj Tripathi", "Cardiologist", "MBBS, DM (Cardiology)", "Heart care clinic, Gorakhpur Road", 16, 700, "Hindi, English", [0, 2, 4], MORN),
    ("Meena Pandey", "Dentist", "BDS, MDS", "Smile dental clinic, Gandhi Chowk", 7, 350, "Hindi, English", range(6), MORN + AFT),
    ("Sanjay Gupta", "Orthopaedic Surgeon", "MBBS, MS (Orthopaedics)", "Bone & joint clinic, Nichlaul Road", 13, 600, "Hindi, English", [1, 3, 5], MORN + AFT),
    ("Anjali Yadav", "ENT Specialist", "MBBS, MS (ENT)", "ENT care centre, Civil Lines", 10, 450, "Hindi, English", range(5), MORN),
]


def sample_report_pdf(patient_name, lab_name):
    """A simple one-page PDF so the 'digital report' flow can be shown end to end."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1240, 1754), "white")
    d = ImageDraw.Draw(img)
    try:
        big, mid, small = (ImageFont.load_default(size=s) for s in (46, 30, 24))
    except TypeError:
        big = mid = small = ImageFont.load_default()
    d.rectangle([0, 0, 1240, 150], fill=(20, 69, 107))
    d.text((60, 45), lab_name, fill="white", font=big)
    d.text((60, 190), "Complete Blood Count", fill=(20, 69, 107), font=big)
    d.text((60, 270), f"Patient: {patient_name}", fill=(21, 41, 59), font=mid)
    d.text((60, 315), f"Reported on: {timezone.localdate():%d %b %Y}", fill=(21, 41, 59), font=mid)
    rows = [("Test", "Result", "Reference range"), ("Haemoglobin", "13.8 g/dL", "13.0 – 17.0"),
            ("Total WBC count", "7,200 /µL", "4,000 – 11,000"), ("Platelet count", "2.4 lakh /µL", "1.5 – 4.1"),
            ("RBC count", "4.9 million/µL", "4.5 – 5.5"), ("Haematocrit", "42 %", "40 – 50")]
    y = 420
    for i, (a, b, c) in enumerate(rows):
        if i == 0:
            d.rectangle([60, y - 10, 1180, y + 44], fill=(230, 241, 250))
        for x, text in zip((80, 520, 840), (a, b, c)):
            d.text((x, y), text, fill=(21, 41, 59), font=mid)
        y += 70
    d.text((60, y + 40), "Values shown are illustrative. Please discuss all results with your doctor.", fill=(91, 107, 121), font=small)
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=150)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Loads starting data (tests, nearby labs, doctors). Safe to run many times. Edit or replace everything from the admin panel."

    def add_arguments(self, parser):
        parser.add_argument("--sample-accounts", metavar="PASSWORD",
                            help="Also create sample logins (doctor1, lab1, patient1, plus a pending doctor2 and lab2) and sample activity.")

    def handle(self, *args, **opts):
        tests = {}
        for name, cat, desc, prep in TESTS:
            tests[name], _ = Test.objects.get_or_create(name=name, defaults={"category": cat, "description": desc, "preparation": prep})

        labs = {}
        for name, area, address, phone, dist, home, hours, prices in LABS:
            lab, _ = Lab.objects.get_or_create(name=name, defaults={
                "area": area, "address": address, "phone": phone, "distance_km": Decimal(dist),
                "home_collection": home, "opening_hours": hours})
            labs[name] = lab
            for test_name, (price, hours_) in prices.items():
                LabTest.objects.get_or_create(lab=lab, test=tests[test_name], defaults={"price": price, "turnaround_hours": hours_})

        doctors = []
        for name, spec, qual, clinic, years, fee, langs, days, times in DOCTORS:
            doc, _ = Doctor.objects.get_or_create(name=name, defaults={
                "specialization": spec, "qualification": qual, "clinic": clinic, "experience_years": years,
                "consultation_fee": fee, "languages": langs,
                "bio": f"{spec} with {years} years of experience, available for online consultations and follow-ups."})
            doctors.append(doc)
            for weekday in days:
                for t in times:
                    DoctorSlot.objects.get_or_create(doctor=doc, weekday=weekday, start_time=t)
        self.stdout.write(self.style.SUCCESS(f"Ready: {len(tests)} tests, {len(labs)} labs, {len(doctors)} doctors."))

        password = opts.get("sample_accounts")
        if password:
            self._sample_accounts(password, doctors, labs, tests)

    def _sample_accounts(self, password, doctors, labs, tests):
        def make(username, role, first, last, **extra):
            user, created = User.objects.get_or_create(username=username, defaults={
                "role": role, "first_name": first, "last_name": last, "email": f"{username}@example.com", **extra})
            if created:
                user.set_password(password)
                user.save()
            return user

        kavita = doctors[0]
        main_lab = labs["Maharajganj Diagnostic Centre"]
        Doctor.objects.filter(pk=kavita.pk, user__isnull=True).update(user=make("doctor1", "doctor", "Kavita", "Shukla", phone="9000000001"))
        Lab.objects.filter(pk=main_lab.pk, user__isnull=True).update(user=make("lab1", "lab", "Maharajganj", "Diagnostic", phone="9000000002"))
        patient = make("patient1", "patient", "Aarav", "Sharma", phone="9000000000")

        # a doctor and a lab that registered themselves and wait for admin approval
        pending_doc_user = make("doctor2", "doctor", "Neha", "Gupta", phone="9000000003")
        pending_doc, _ = Doctor.objects.get_or_create(user=pending_doc_user, defaults={
            "name": "Neha Gupta", "specialization": "Physiotherapist", "qualification": "BPT, MPT",
            "registration_number": "UP-PT-20418", "clinic": "Active physio clinic, Civil Lines",
            "experience_years": 5, "consultation_fee": 350, "is_verified": False})
        for weekday in range(5):
            DoctorSlot.objects.get_or_create(doctor=pending_doc, weekday=weekday, start_time=time(10, 0))
        pending_lab_user = make("lab2", "lab", "Ravi", "Singh", phone="9000000004")
        Lab.objects.get_or_create(user=pending_lab_user, defaults={
            "name": "Medico Path Lab", "area": "Tehsil Road", "address": "Tehsil Road, Maharajganj", "phone": "9415000199",
            "license_number": "UP-LAB-77120", "is_verified": False})

        # patient activity so every dashboard and the admin queues have something to show
        today = timezone.localdate()
        Appointment.objects.get_or_create(
            patient=patient, doctor=kavita, date=today - timedelta(days=10), time=time(10, 0),
            defaults={"status": "completed", "mode": "online", "reason": "Tiredness and weakness for two weeks.",
                      "doctor_advice": "Get a complete blood count done and drink plenty of water. Review the report with me after the test."})
        Appointment.objects.get_or_create(
            patient=patient, doctor=kavita, date=today + timedelta(days=1), time=time(10, 30),
            defaults={"status": "confirmed", "kind": "follow_up", "mode": "online", "reason": "Review of blood report."})
        Appointment.objects.get_or_create(
            patient=patient, doctor=doctors[1], date=today + timedelta(days=3), time=time(11, 0),
            defaults={"status": "requested", "mode": "clinic", "reason": "Routine check-up."})

        cbc = LabTest.objects.get(lab=main_lab, test=tests["Complete Blood Count"])
        done_appt = Appointment.objects.filter(patient=patient, doctor=kavita, status="completed").first()
        tr, _ = TestRequest.objects.get_or_create(
            patient=patient, lab_test=cbc, preferred_date=today - timedelta(days=8),
            defaults={"appointment": done_appt, "collection_type": "home", "address": "House 12, Civil Lines, Maharajganj",
                      "status": "collected", "scheduled_slot": "7–9 AM"})
        if not Report.objects.filter(test_request=tr).exists():
            rep = Report(test_request=tr, summary="All values are within the reference range.", reviewed_by=kavita,
                         doctor_remarks="Report looks fine. Continue a balanced diet and book a follow-up if tiredness continues.",
                         reported_on=today - timedelta(days=7))
            rep.file.save("cbc-report.pdf", ContentFile(sample_report_pdf(patient.display_name, main_lab.name)), save=False)
            rep.save()
        lipid = LabTest.objects.get(lab=labs["CityCare Pathology"], test=tests["Lipid Profile"])
        TestRequest.objects.get_or_create(
            patient=patient, lab_test=lipid, preferred_date=today + timedelta(days=2),
            defaults={"collection_type": "home", "address": "House 12, Civil Lines, Maharajganj"})

        self.stdout.write(self.style.WARNING(
            f"Sample logins (password: {password}): patient1, doctor1, lab1. Pending approval: doctor2, lab2. "
            "Delete these accounts from the admin panel before going live."))
