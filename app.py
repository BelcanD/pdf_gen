from flask import Flask, render_template_string, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from PIL import Image, ImageDraw
import base64
import os
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_temp_photo(file):
    if file and allowed_file(file.filename):
        # Create a temporary file with the same extension
        ext = file.filename.rsplit('.', 1)[1].lower()
        temp_file = tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False)
        file.save(temp_file.name)
        return temp_file.name
    return None

def cleanup_temp_file(filepath):
    try:
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)
    except Exception as e:
        print(f"Error cleaning up temp file: {e}")

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

def create_pdf(data, photo_path=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add black sidebar
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.rect(0, 0, width/3, height, fill=1)
    
    # Calculate photo dimensions and position
    photo_size = int(width/3 - 40)
    photo_x = 20
    photo_y = height - photo_size - 20
    
    # Draw white circle background
    c.setFillColorRGB(1, 1, 1)
    c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2, fill=1)
    
    # Handle photo if provided
    if photo_path and os.path.exists(photo_path):
        try:
            img = Image.open(photo_path)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Make square
            size = min(img.size)
            left = (img.size[0] - size) // 2
            top = (img.size[1] - size) // 2
            img = img.crop((left, top, left + size, top + size))
            
            # Create mask
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            
            # Apply mask and resize
            output = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            output.paste(img, (0, 0))
            output.putalpha(mask)
            output = output.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
            
            # Save to temporary buffer
            temp_buffer = BytesIO()
            output.save(temp_buffer, format='PNG')
            temp_buffer.seek(0)
            
            # Draw in PDF
            c.drawImage(temp_buffer, photo_x, photo_y, photo_size, photo_size, mask='auto')
            
        except Exception as e:
            print(f"Error processing photo: {e}")
    
    # Rest of the PDF content
    // ... existing code ...

@app.route('/')
def home():
    return render_template_string(template)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    temp_filepath = None
    try:
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

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                temp_filepath = save_temp_photo(file)

        pdf = create_pdf(data, temp_filepath)
        
        return send_file(
            pdf,
            download_name='resume.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return f"An error occurred while generating the PDF: {e}", 500
    finally:
        if temp_filepath:
            cleanup_temp_file(temp_filepath)

if __name__ == '__main__':
    app.run(debug=True) 