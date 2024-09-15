import streamlit as st
import openai
import json
import subprocess
import os
from PyPDF2 import PdfReader

# Define function to extract text from PDF
# Define function to extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
            else:
                st.warning("No text found on a page.")
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
    return text


# Set your OpenAI API key
openai.api_key = "" # Replace with your actual API key

def generate_suggestions(text):
    try:
        # Call OpenAI API for generating suggestions
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Here is the text of a resume. Please suggest improvements to the resume, do not print the resume contents again but only the suggestions:\n\n{text}"}
            ]
        )
        return response.choices[0].message
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return None

def convert_resume_to_json(text):
    try:
        # Call OpenAI API for generating suggestions
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume creator who transforms lives by crafting winning resumes."},
                {"role": "user", "content": f"""Here is the text of a resume. Please generate a json load of the resume,the format should contain only provide JSON 
                 nothing else as the response the json in the following format 
                 Here is an example format:\n{{\n'name': 'John Doe',\n'email': 'john.doe@example.com',\n'address': '123 Main St, Anytown, USA',\n'phone': '123-456-7890',\n'experience': 
                 [\n{{\n'company': 'Company A',\n'title': 'Position A',\n'duration': 'Jan 2020 - Present',\n'location': 'City, Country',\n'description': [\n'Responsibility 1',\n'Responsibility 2'\n]\n}}
                 ,\n{{\n'company': 'Company B',\n'title': 'Position B',\n'duration': 'Jan 2018 - Dec 2019',\n'location': 'City, Country',\n'description': [\n'Responsibility 1',\n'Responsibility 2'\n]\n}}\n]
                 ,\n'education': [\n{{\n'university': 'University A',\n'degree': 'Degree A',\n'year': '2014 - 2018',\n'location': 'City, Country'\n}}\n],\n'projects': [\n{{\n'title': 'Project A',\n'description': 
                 'Description of Project A',\n'link': 'http://example.com'\n}}\n],\n'skills': [\n'Skill 1',\n'Skill 2'\n]\n}}
                 ,ignore any errors in provided example of json format:\n\n{text} 
                Do not assume that you will get all the information in the same order as in the json, things can be mixed up, use your judgement and craft each secton beautifully
                A project detail section of atleast 500 words is a must have, find the same in the resume and expand on it as needed
                Total resume length should be atleast 10000 words
             
            """}
            ]
        )
        # Extract the text from the response
        json_output = response.choices[0].message
        # Parse the JSON string to a Python dictionary
        parsed_json = json.loads(json_output.content)
        return parsed_json
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return None

# Define Streamlit UI
st.title('Resume Improvement and Conversion')

# File uploader
uploaded_file = st.file_uploader("Upload your resume (PDF format)", type=["pdf"])

if uploaded_file:
    # Extract text from the PDF
    resume_text = extract_text_from_pdf(uploaded_file)

    # Display extracted text for debugging
    if resume_text:
        st.subheader('Extracted Resume Text')
        st.text_area('Resume Text', resume_text, height=300)
  
    
    
    # Generate improvement suggestions using OpenAI API
    try:
        suggestions = generate_suggestions(resume_text)
        st.subheader('Suggested Improvements')
        st.text_area('Improvements Suggested by AI', suggestions, height=300)

        # Allow user to accept or reject suggestions
        accept_suggestions = st.radio(
            "Do you want to apply these suggestions to your resume?",
            ("Yes", "No")
        )
        
        if accept_suggestions == "Yes":
            st.success('Applying suggestions...')
            
            # Assume suggestions are directly applied to resume_text for simplicity
            # In practice, you'd need to parse and apply the suggestions correctly
            # For demonstration, we'll use the original text
            updated_resume_text = resume_text  # Update this with actual applied changes
            
            # Convert updated resume text to JSON using OpenAI API
            resume_json = convert_resume_to_json(updated_resume_text)
            
            # Save JSON file
            with open("data.json", "w") as json_file:
                json.dump(resume_json, json_file, indent=4)
            
            st.success('JSON file created successfully!')

            # Run the external script (main.py)
            try:
                subprocess.run(["python", "main.py"], check=True)
                st.success('Resume processing complete!')
            except subprocess.CalledProcessError as e:
                st.error(f"Error running main.py: {e}")
            
            # Provide download link for the generated resume
            if os.path.exists("anonymous_resume.pdf"):
                with open("anonymous_resume.pdf", "rb") as f:
                    st.download_button(
                        label="Download Processed Resume",
                        data=f,
                        file_name="anonymous_resume.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("Processed resume file not found.")
        else:
            st.info('You have chosen not to apply the suggestions.')
    
    except Exception as e:
        st.error(f"Error generating suggestions or JSON from resume: {e}")
