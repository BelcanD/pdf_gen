from flask import Flask, render_template_string, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from PIL import Image
import base64

app = Flask(__name__)

template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Creator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 2rem;
            color: #333;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        h1 {
            text-align: center;
            margin-bottom: 2rem;
            color: #000;
            font-size: 2.5rem;
        }

        .photo-upload {
            text-align: center;
            margin-bottom: 2rem;
        }

        .photo-preview {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            margin: 1rem auto;
            border: 3px solid #000;
            overflow: hidden;
            position: relative;
        }

        .photo-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .photo-upload input[type="file"] {
            display: none;
        }

        .photo-upload label {
            background: #000;
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            cursor: pointer;
            display: inline-block;
            margin-top: 1rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
            background: #fff;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
            color: #333;
        }

        input, textarea {
            width: 100%;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            background: #f8f9fa;
        }

        .education-entry, .experience-entry {
            background: #f8f9fa;
            border: 1px solid #ddd;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            position: relative;
        }

        .timeline-line {
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #000;
        }

        .timeline-dot {
            position: absolute;
            left: -24px;
            top: 20px;
            width: 10px;
            height: 10px;
            background: #000;
            border-radius: 50%;
        }

        button {
            background: #000;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }

        button:hover {
            background: #333;
            transform: translateY(-2px);
        }

        .add-btn {
            background: #28a745;
            margin-bottom: 1rem;
        }

        .add-btn:hover {
            background: #218838;
        }

        .skill-bars {
            list-style: none;
            padding: 0;
        }

        .skill-bar {
            margin-bottom: 1rem;
        }

        .skill-name {
            display: block;
            margin-bottom: 0.5rem;
        }

        .skill-level {
            height: 10px;
            background: #eee;
            border-radius: 5px;
            overflow: hidden;
        }

        .skill-level-fill {
            height: 100%;
            background: #000;
            border-radius: 5px;
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
        <h1>PDF Creator</h1>
        <form action="/generate" method="POST" enctype="multipart/form-data">
            <div class="photo-upload">
                <div class="photo-preview">
                    <img id="preview" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" alt="Preview">
                </div>
                <label for="photo">Upload Photo</label>
                <input type="file" id="photo" name="photo" accept="image/*" onchange="previewImage(this)">
            </div>

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
            
            <div id="education-container" class="form-group">
                <h3>Education</h3>
                <button type="button" class="add-btn" onclick="addEducation()">Add Education</button>
                <div class="education-entry">
                    <div class="timeline-line"></div>
                    <div class="timeline-dot"></div>
                    <input type="text" name="edu_years[]" placeholder="Years (e.g., 2011-2014)" required>
                    <input type="text" name="edu_school[]" placeholder="School/University" required>
                    <input type="text" name="edu_location[]" placeholder="Location" required>
                </div>
            </div>
            
            <div id="experience-container" class="form-group">
                <h3>Experience</h3>
                <button type="button" class="add-btn" onclick="addExperience()">Add Experience</button>
                <div class="experience-entry">
                    <div class="timeline-line"></div>
                    <div class="timeline-dot"></div>
                    <input type="text" name="exp_years[]" placeholder="Years (e.g., 2018-2020)" required>
                    <input type="text" name="exp_position[]" placeholder="Position" required>
                    <textarea name="exp_description[]" placeholder="Description" required></textarea>
                </div>
            </div>
            
            <div class="form-group">
                <h3>Skills/Expertise</h3>
                <div id="skills-container">
                    <div class="skill-entry">
                        <input type="text" name="skill_names[]" placeholder="Skill name" required>
                        <input type="range" name="skill_levels[]" min="0" max="100" value="50" class="skill-range" required>
                    </div>
                </div>
                <button type="button" class="add-btn" onclick="addSkill()">Add Skill</button>
            </div>
            
            <button type="submit">Generate PDF</button>
        </form>
    </div>

    <script>
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('preview').src = e.target.result;
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        function addEducation() {
            const container = document.getElementById('education-container');
            const entry = document.createElement('div');
            entry.className = 'education-entry';
            entry.innerHTML = `
                <div class="timeline-line"></div>
                <div class="timeline-dot"></div>
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
                <div class="timeline-line"></div>
                <div class="timeline-dot"></div>
                <input type="text" name="exp_years[]" placeholder="Years" required>
                <input type="text" name="exp_position[]" placeholder="Position" required>
                <textarea name="exp_description[]" placeholder="Description" required></textarea>
            `;
            container.appendChild(entry);
        }

        function addSkill() {
            const container = document.getElementById('skills-container');
            const entry = document.createElement('div');
            entry.className = 'skill-entry';
            entry.innerHTML = `
                <input type="text" name="skill_names[]" placeholder="Skill name" required>
                <input type="range" name="skill_levels[]" min="0" max="100" value="50" class="skill-range" required>
            `;
            container.appendChild(entry);
        }
    </script>
</body>
</html>
"""

def create_pdf(data, photo=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add black sidebar
    c.setFillColorRGB(0.1, 0.1, 0.1)  # Dark gray/black
    c.rect(0, 0, width/3, height, fill=1)
    
    # Add photo if provided
    if photo:
        img = Image.open(photo)
        # Crop to square
        size = min(img.size)
        left = (img.size[0] - size) // 2
        top = (img.size[1] - size) // 2
        img = img.crop((left, top, left + size, top + size))
        # Resize to fit
        img = img.resize((int(width/3 - 40), int(width/3 - 40)))
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Calculate position for centered photo
        photo_x = 20
        photo_y = height - (width/3 - 20)
        c.drawImage(img_buffer, photo_x, photo_y, width/3 - 40, width/3 - 40)
    
    # Start content below photo
    y_position = height - (width/3 + 20)
    
    # Add content to sidebar (white text)
    c.setFillColorRGB(1, 1, 1)  # White color
    
    # About me section
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y_position, "About me")
    y_position -= 25
    
    # Split about text into multiple lines
    c.setFont("Helvetica", 10)
    words = data['about'].split()
    line = ""
    for word in words:
        if len(line + word) < 25:
            line += word + " "
        else:
            c.drawString(20, y_position, line)
            y_position -= 15
            line = word + " "
    if line:
        c.drawString(20, y_position, line)
    
    # Contact section
    y_position -= 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y_position, "Contact")
    y_position -= 25
    
    c.setFont("Helvetica", 10)
    c.drawString(20, y_position, data['phone'])
    y_position -= 15
    c.drawString(20, y_position, data['email'])
    y_position -= 15
    c.drawString(20, y_position, data['address'])
    
    # Expertise section
    y_position -= 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y_position, "Expertise")
    y_position -= 25
    
    # Draw skill bars
    c.setFont("Helvetica", 10)
    for name, level in zip(data['skill_names'], data['skill_levels']):
        c.drawString(20, y_position, name)
        # Draw skill bar background
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.rect(20, y_position - 10, 80, 5, fill=1)
        # Draw skill level
        c.setFillColorRGB(1, 1, 1)
        level_width = (float(level) / 100) * 80
        c.rect(20, y_position - 10, level_width, 5, fill=1)
        y_position -= 25

    # Main content area (right side)
    right_margin = width/3 + 40
    y_position = height - 100
    
    # Name and title
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(right_margin, y_position, data['name'])
    y_position -= 30
    c.setFont("Helvetica", 16)
    c.drawString(right_margin, y_position, data['title'])
    y_position -= 50

    # Education section
    c.setFont("Helvetica-Bold", 18)
    c.drawString(right_margin, y_position, "Education")
    y_position -= 30
    
    for i in range(len(data['edu_years'])):
        # Timeline dot
        c.circle(right_margin - 15, y_position + 5, 3, fill=1)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(right_margin, y_position, data['edu_years'][i])
        c.setFont("Helvetica", 10)
        c.drawString(right_margin, y_position-15, data['edu_school'][i])
        c.drawString(right_margin, y_position-30, data['edu_location'][i])
        y_position -= 50

    # Experience section
    y_position -= 20
    c.setFont("Helvetica-Bold", 18)
    c.drawString(right_margin, y_position, "Experience")
    y_position -= 30
    
    for i in range(len(data['exp_years'])):
        # Timeline dot
        c.circle(right_margin - 15, y_position + 5, 3, fill=1)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(right_margin, y_position, data['exp_years'][i])
        c.setFont("Helvetica", 10)
        c.drawString(right_margin, y_position-15, data['exp_position'][i])
        
        # Split description into multiple lines
        words = data['exp_description'][i].split()
        line = ""
        desc_y = y_position-30
        for word in words:
            if len(line + word) < 50:
                line += word + " "
            else:
                c.drawString(right_margin, desc_y, line)
                desc_y -= 15
                line = word + " "
        if line:
            c.drawString(right_margin, desc_y, line)
        y_position = desc_y - 30

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
        'skill_names': request.form.getlist('skill_names[]'),
        'skill_levels': request.form.getlist('skill_levels[]')
    }
    
    photo = request.files.get('photo')
    pdf = create_pdf(data, photo)
    
    return send_file(
        pdf,
        download_name='document.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True) 