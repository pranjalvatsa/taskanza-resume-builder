import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PyPDF2 import PdfReader
from openai import OpenAI
import json
import subprocess
import os
import io

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key="xxx")

def extract_text_from_pdf(file):
    text = ""
    try:
        pdf_reader = PdfReader(io.BytesIO(file.file.read()))
        for page in pdf_reader.pages:
            text += page.extract_text()
        logger.info(f"Successfully extracted text from PDF. Text length: {len(text)}")
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading PDF file: {str(e)}")

def generate_suggestions(text):
    try:
        logger.info(f"Generating suggestions for text of length: {len(text)}")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Here is the text of a resume. Please suggest improvements to the resume in a list format in JSON:\n\n{text}"}
            ]
        )
        logger.info("Received response from OpenAI")
        
        logger.debug(f"Raw response content: {response.choices[0].message.content}")
        
        suggestions = json.loads(response.choices[0].message.content)
        logger.info("Successfully parsed suggestions JSON")
        return suggestions
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse JSON: {str(json_err)}")
        logger.error(f"Problematic content: {response.choices[0].message.content}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON in OpenAI response: {str(json_err)}")
    except Exception as e:
        logger.error(f"Error in generate_suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")

def convert_resume_to_json(text, selected_suggestions=None):
    try:
        if selected_suggestions:
            suggestions_text = "\n".join([f"- {s}" for s in selected_suggestions])
            prompt = f"Here is the resume text enhanced with the following suggestions:\n\n{suggestions_text}\n\n{text}"
        else:
            prompt = text

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume creator."},
                {"role": "user", "content": f"""Here is the resume text and the selected suggestions. Generate a JSON format of the resume. 
                The JSON format should follow this structure: 
                {{'name': 'John Doe', 'email': 'john.doe@example.com', 'experience': [...]}} 
                ignoring any errors, and use the following resume text and suggestions:\n\n{prompt}"""}
            ]
        )
        logger.info("Received response from OpenAI for JSON conversion")
        
        resume_json = json.loads(response.choices[0].message.content)
        logger.info("Successfully converted resume to JSON")
        return resume_json
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse JSON: {str(json_err)}")
        logger.error(f"Problematic content: {response.choices[0].message.content}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON in OpenAI response: {str(json_err)}")
    except Exception as e:
        logger.error(f"Error converting resume to JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting resume to JSON: {str(e)}")

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    if not file.filename.endswith(".pdf"):
        logger.warning(f"Rejected non-PDF file: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    resume_text = extract_text_from_pdf(file)
    if not resume_text:
        logger.warning(f"No text extracted from PDF: {file.filename}")
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")

    suggestions = generate_suggestions(resume_text)
    resume_json = convert_resume_to_json(resume_text)

    with open("data.json", "w") as json_file:
        json.dump(resume_json, json_file, indent=4)
    logger.info("Resume processed and saved to data.json")

    return {
        "message": "Resume uploaded and processed successfully.",
        "suggestions": suggestions,
        "json_output": resume_json
    }

class SuggestionRequest(BaseModel):
    resume_text: str
    selected_suggestions: list[str]

@app.post("/apply-suggestions/")
async def apply_suggestions(request: SuggestionRequest):
    logger.info("Received request to apply suggestions")
    resume_json = convert_resume_to_json(request.resume_text, request.selected_suggestions)
    
    with open("data.json", "w") as json_file:
        json.dump(resume_json, json_file, indent=4)
    logger.info("Updated resume saved to data.json")
    
    try:
        subprocess.run(["python", "main.py"], check=True)
        logger.info("Successfully ran main.py")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running main.py: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running main.py: {str(e)}")
    
    output_file = "anonymous_resume.pdf"
    if os.path.exists(output_file):
        logger.info(f"Returning processed file: {output_file}")
        return FileResponse(output_file, media_type='application/pdf', filename="anonymous_resume.pdf")
    else:
        logger.error(f"Processed resume file not found: {output_file}")
        raise HTTPException(status_code=500, detail="Processed resume file not found.")

@app.get("/")
async def root():
    return {"message": "Resume processing API is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=8000)