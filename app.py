# app.py

from flask import Flask, render_template, request, send_file
import openai
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def generate_prompt(name, address, subject, letter_type, body):
    templates = {
        "RTI": """
You are an expert in drafting formal Indian government letters.
Draft a Right to Information (RTI) request letter using this information:

Name: {name}
Address: {address}
Subject: {subject}
Details: {body}

Use formal tone, proper formatting, and government norms.
""",
        "Police Complaint": """
You are an expert in drafting formal Indian government letters.
Draft a police complaint letter using this information:

Name: {name}
Address: {address}
Subject: {subject}
Details: {body}

Use a polite but firm tone and proper format.
""",
        "Leave Application": """
You are an expert in drafting formal Indian government letters.
Draft a leave application using this information:

Name: {name}
Address: {address}
Subject: {subject}
Details: {body}

Use a polite and precise tone.
"""
    }

    template = templates.get(letter_type, "")
    prompt = template.format(name=name, address=address, subject=subject, body=body)
    return prompt

@app.route('/')
def home():
    return render_template('letter_form.html')

@app.route('/generate', methods=['POST'])
def generate_letter():
    # Capture form data using your defined form field names
    name = request.form['name']
    address = request.form['address']
    subject = request.form['subject']
    letter_type = request.form['letter_type']
    body = request.form['body']

    # Generate prompt for OpenAI
    prompt = generate_prompt(name, address, subject, letter_type, body)

    try:
        # Call OpenAI Chat Completion
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.5
        )
        letter_text = response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating letter: {e}"

    # Generate PDF from letter_text
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=LETTER)
    text_object = c.beginText(50, 750)
    text_object.setFont("Times-Roman", 12)

    # Basic line wrap for PDF
    max_line_length = 90
    for paragraph in letter_text.split("\n\n"):
        for line in paragraph.split("\n"):
            # Wrap long lines manually
            while len(line) > max_line_length:
                text_object.textLine(line[:max_line_length])
                line = line[max_line_length:]
            text_object.textLine(line)
        text_object.textLine("")  # Add a blank line between paragraphs

    c.drawText(text_object)
    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    # Send PDF as downloadable file
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="government_letter.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
