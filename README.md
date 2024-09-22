streanlit run app.py


Example Request and Response:
Upload Resume (PDF)
Request:
bash
Copy code
POST /upload-resume/
Content-Type: multipart/form-data

file: resume.pdf

Response:
json
Copy code
{
    "resume_text": "Extracted resume text here...",
    "suggestions": [
        {"suggestion": "Improve the formatting of your experience section."},
        {"suggestion": "Highlight key achievements in each job."}
    ]
}

Apply Selected Suggestions
Request:
bash
Copy code
POST /apply-suggestions/
Content-Type: application/json

{
    "resume_text": "Extracted resume text here...",
    "selected_suggestions": [
        {"suggestion": "Improve the formatting of your experience section."}
    ]
}

Response:
json
Copy code
{
    "resume_json": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "experience": [
            {
                "company": "Company A",
                "title": "Position A",
                "duration": "Jan 2020 - Present",
                "location": "City, Country",
                "description": ["Improved the formatting of experience section."]
            }
        ],
        "education": [...],
        "skills": [...]
    }
}
