import requests
import json

# API endpoint
url = "http://127.0.0.1:5000/api/candidates"

# Sample candidates
candidates = [
    # Data Scientists
    {
        "first_name": "Alice",
        "last_name": "Smith",
        "birthdate": "1990-05-10",
        "age": 34,
        "email": "alice.smith@example.com",
        "phone": "+1234567891",
        "address": "123 Data Lane, Datatown, USA",
        "skills": ["Python", "Machine Learning", "SQL", "Flask"],
        "experiences": [
            {"company": "Data Corp", "role": "Junior Data Scientist", "start_date": "2017-06-01", "end_date": "2020-08-01"},
            {"company": "AI Solutions", "role": "Senior Data Scientist", "start_date": "2020-09-01", "end_date": None}
        ],
        "education": [
            {"institution": "Tech University", "degree": "M.Sc. in Data Science", "year_of_graduation": 2017}
        ]
    },
    {
        "first_name": "Bob",
        "last_name": "Jones",
        "birthdate": "1988-12-15",
        "age": 35,
        "email": "bob.jones@example.com",
        "phone": "+1234567892",
        "address": "456 Science Ave, SciCity, USA",
        "skills": ["Python", "R", "Statistics", "Flask"],
        "experiences": [
            {"company": "Big Data Ltd.", "role": "Data Analyst", "start_date": "2015-01-01", "end_date": "2018-12-31"},
            {"company": "Insight Analytics", "role": "Data Scientist", "start_date": "2019-01-01", "end_date": None}
        ],
        "education": [
            {"institution": "University of Analysis", "degree": "B.Sc. in Statistics", "year_of_graduation": 2015}
        ]
    },
    # Math Teachers
    {
        "first_name": "Carol",
        "last_name": "Davis",
        "birthdate": "1985-08-21",
        "age": 39,
        "email": "carol.davis@example.com",
        "phone": "+1234567893",
        "address": "789 Math Road, Calculus City, USA",
        "skills": ["Mathematics", "Algebra", "Teaching"],
        "experiences": [
            {"company": "High School #1", "role": "Math Teacher", "start_date": "2010-09-01", "end_date": "2018-06-30"},
            {"company": "High School #2", "role": "Senior Math Teacher", "start_date": "2018-09-01", "end_date": None}
        ],
        "education": [
            {"institution": "Education College", "degree": "B.Ed. in Mathematics", "year_of_graduation": 2010}
        ]
    },
    {
        "first_name": "David",
        "last_name": "Clark",
        "birthdate": "1983-03-14",
        "age": 41,
        "email": "david.clark@example.com",
        "phone": "+1234567894",
        "address": "321 Geometry Ave, Mathsland, USA",
        "skills": ["Mathematics", "Calculus", "Geometry"],
        "experiences": [
            {"company": "Middle School", "role": "Math Teacher", "start_date": "2008-09-01", "end_date": "2015-06-30"},
            {"company": "Community High School", "role": "Math Department Head", "start_date": "2015-09-01", "end_date": None}
        ],
        "education": [
            {"institution": "University of Teaching", "degree": "M.Ed. in Secondary Education", "year_of_graduation": 2008}
        ]
    },
    # Doctors
    {
        "first_name": "Evelyn",
        "last_name": "Brown",
        "birthdate": "1979-11-11",
        "age": 45,
        "email": "evelyn.brown@example.com",
        "phone": "+1234567895",
        "address": "654 Health Blvd, Wellness City, USA",
        "skills": ["Medicine", "Surgery", "Patient Care"],
        "experiences": [
            {"company": "City Hospital", "role": "Resident Doctor", "start_date": "2005-07-01", "end_date": "2010-07-01"},
            {"company": "Health Clinic", "role": "General Practitioner", "start_date": "2010-08-01", "end_date": None}
        ],
        "education": [
            {"institution": "Medical School", "degree": "M.D.", "year_of_graduation": 2005}
        ]
    },
    {
        "first_name": "Frank",
        "last_name": "Wilson",
        "birthdate": "1976-06-30",
        "age": 48,
        "email": "frank.wilson@example.com",
        "phone": "+1234567896",
        "address": "987 Medical Rd, MediTown, USA",
        "skills": ["Medicine", "Pediatrics", "Emergency Care"],
        "experiences": [
            {"company": "County Hospital", "role": "ER Doctor", "start_date": "2006-01-01", "end_date": "2016-12-31"},
            {"company": "Children's Clinic", "role": "Pediatrician", "start_date": "2017-01-01", "end_date": None}
        ],
        "education": [
            {"institution": "Medical Institute", "degree": "M.D. in Pediatrics", "year_of_graduation": 2006}
        ]
    }
]

# Sending data to API
for candidate in candidates:
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(candidate))
    print(response.json())
