from flask import Flask, render_template_string, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from io import BytesIO
import os

app = Flask(__name__)

# HTML template with form
template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
            color: #333;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        h1 {
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }

        input, textarea {
            width: 100%;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }

        .education-entry, .experience-entry {
            border: 1px solid #ddd;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
        }

        button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            width: 100%;
            font-size: 1.1rem;
            transition: transform 0.3s ease;
        }

        button:hover {
            transform: translateY(-2px);
        }

        .add-btn {
            background: #28a745;
            margin-bottom: 1rem;
        }

        @media (max-width: 480px) {
            .container {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CV Generator</h1>
        <form action="/generate" method="POST">
            <div class="form-group">
                <label>Full Name</label>
                <input type="text" name="name" required>
            </div>
            
            <div class="form-group">
                <label>Title/Position</label>
                <input type="text" name="title" required>
            </div>
            
            <div class="form-group">
                <label>About Me</label>
                <textarea name="about" rows="4" required></textarea>
            </div>
            
            <div class="form-group">
                <label>Contact Information</label>
                <input type="tel" name="phone" placeholder="Phone" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="text" name="address" placeholder="Address" required>
            </div>
            
            <div id="education-container">
                <h3>Education</h3>
                <button type="button" class="add-btn" onclick="addEducation()">Add Education</button>
                <div class="education-entry">
                    <input type="text" name="edu_years[]" placeholder="Years (e.g., 2011-2014)" required>
                    <input type="text" name="edu_school[]" placeholder="School/University" required>
                    <input type="text" name="edu_location[]" placeholder="Location" required>
                </div>
            </div>
            
            <div id="experience-container">
                <h3>Work Experience</h3>
                <button type="button" class="add-btn" onclick="addExperience()">Add Experience</button>
                <div class="experience-entry">
                    <input type="text" name="exp_years[]" placeholder="Years (e.g., 2018-2020)" required>
                    <input type="text" name="exp_position[]" placeholder="Position" required>
                    <textarea name="exp_description[]" placeholder="Description" required></textarea>
                </div>
            </div>
            
            <div class="form-group">
                <h3>Expertise/Skills</h3>
                <textarea name="skills" rows="4" placeholder="Enter skills (one per line)" required></textarea>
            </div>
            
            <button type="submit">Generate PDF</button>
        </form>
    </div>

    <script>
        function addEducation() {
            const container = document.getElementById('education-container');
            const entry = document.createElement('div');
            entry.className = 'education-entry';
            entry.innerHTML = `
                <input type="text" name="edu_years[]" placeholder="Years" required>
                <input type="text" name="edu_school[]" placeholder="School/University" required>
                <input type="text" name="edu_location[]" placeholder="Location" required>
            `;
            container.appendChild(entry);
        }

        function addExperience() {
            const container = document.getElementById('experience-container');
            const entry = document.createElement('div');
            entry.className = 'experience-entry';
            entry.innerHTML = `
                <input type="text" name="exp_years[]" placeholder="Years" required>
                <input type="text" name="exp_position[]" placeholder="Position" required>
                <textarea name="exp_description[]" placeholder="Description" required></textarea>
            `;
            container.appendChild(entry);
        }
    </script>
</body>
</html>
"""

def create_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add profile section
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.rect(0, height-250, 200, height, fill=1)
    
    # Add name and title
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(220, height-60, data['name'])
    c.setFont("Helvetica", 16)
    c.drawString(220, height-80, data['title'])

    # Add about me
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, height-280, "About me")
    c.setFont("Helvetica", 10)
    c.drawString(30, height-300, data['about'])

    # Add contact information
    y_position = height-350
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y_position, "Contact")
    c.setFont("Helvetica", 10)
    c.drawString(30, y_position-20, f"Phone: {data['phone']}")
    c.drawString(30, y_position-40, f"Email: {data['email']}")
    c.drawString(30, y_position-60, f"Address: {data['address']}")

    # Add education
    y_position = height-150
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(220, y_position, "Education")
    
    y_position -= 30
    for i in range(len(data['edu_years'])):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(220, y_position, data['edu_years'][i])
        c.setFont("Helvetica", 10)
        c.drawString(220, y_position-15, data['edu_school'][i])
        c.drawString(220, y_position-30, data['edu_location'][i])
        y_position -= 50

    # Add work experience
    y_position -= 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(220, y_position, "Work Experience")
    
    y_position -= 30
    for i in range(len(data['exp_years'])):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(220, y_position, data['exp_years'][i])
        c.setFont("Helvetica", 10)
        c.drawString(220, y_position-15, data['exp_position'][i])
        c.drawString(220, y_position-30, data['exp_description'][i])
        y_position -= 60

    # Add skills
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, height-450, "Expertise")
    y_position = height-480
    for skill in data['skills'].split('\n'):
        c.setFont("Helvetica", 10)
        c.drawString(30, y_position, f"• {skill}")
        y_position -= 20

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return render_template_string(template)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    data = {
        'name': request.form['name'],
        'title': request.form['title'],
        'about': request.form['about'],
        'phone': request.form['phone'],
        'email': request.form['email'],
        'address': request.form['address'],
        'edu_years': request.form.getlist('edu_years[]'),
        'edu_school': request.form.getlist('edu_school[]'),
        'edu_location': request.form.getlist('edu_location[]'),
        'exp_years': request.form.getlist('exp_years[]'),
        'exp_position': request.form.getlist('exp_position[]'),
        'exp_description': request.form.getlist('exp_description[]'),
        'skills': request.form['skills']
    }
    
    pdf = create_pdf(data)
    return send_file(
        pdf,
        download_name='resume.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True) 