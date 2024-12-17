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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def wrap_text(text, width, c, x_pos, y_pos, font_name="Helvetica", font_size=10):
    """
    Wraps text to maximum 25 characters per line
    """
    c.setFont(font_name, font_size)
    words = text.split()
    line = ""
    char_count = 0
    max_chars = 25
    
    for word in words:
        test_line = f"{line} {word}".strip()
        if len(test_line) > max_chars:
            if len(line) > max_chars:
                print(f"Warning: Line exceeds {max_chars} characters: '{line}'")
            if line:
                c.drawString(x_pos, y_pos, line[:max_chars])
                y_pos -= font_size + 4
            line = word
            char_count = len(word)
        else:
            line = test_line
            char_count = len(line)
    
    if line:
        if len(line) > max_chars:
            print(f"Warning: Line exceeds {max_chars} characters: '{line}'")
            c.drawString(x_pos, y_pos, line[:max_chars])
        else:
            c.drawString(x_pos, y_pos, line)
        y_pos -= font_size + 4
    
    return y_pos

# Function for text wrapping with character limit
def wrap_text_with_limit(text, width, c, x_pos, y_pos, font_name="Helvetica", font_size=10):
    c.setFont(font_name, font_size)
    words = text.split()
    line = ""
    max_chars = 25  # Character limit per line
    
    for word in words:
        test_line = f"{line} {word}".strip()
        if len(test_line) > max_chars:
            if line:
                c.drawString(x_pos, y_pos, line[:max_chars])
                y_pos -= font_size + 4
            line = word
        else:
            line = test_line
    
    if line:
        if len(line) > max_chars:
            c.drawString(x_pos, y_pos, line[:max_chars])
        else:
            c.drawString(x_pos, y_pos, line)
        y_pos -= font_size + 4
    
    return y_pos

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

    # Add black sidebar with slightly reduced width
    sidebar_width = width/3 - 10
    c.setFillColorRGB(0.1, 0.1, 0.1)
    
    # Name section dimensions
    name_section_height = 120
    
    # Draw black background as one piece for sidebar and name section
    # First draw the full height sidebar
    c.rect(0, 0, sidebar_width, height, fill=1)
    # Then draw the name section extending from sidebar
    c.rect(sidebar_width, height - name_section_height, width - sidebar_width, name_section_height, fill=1)
    
    # Calculate photo dimensions and position
    photo_size = int(sidebar_width - 40)
    photo_x = 20
    photo_y = height - photo_size - 20
    
    # Handle photo if provided
    if photo:
        try:
            photo.seek(0)
            img = Image.open(photo)
            print(f"Image opened successfully. Mode: {img.mode}, Size: {img.size}")
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to fit the space
            img = img.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
            
            # Save to temporary file
            temp_dir = tempfile.gettempdir()
            temp_img_path = os.path.join(temp_dir, "temp_photo.png")
            img.save(temp_img_path, format='PNG')
            
            # Draw in PDF
            c.drawImage(temp_img_path, photo_x, photo_y, width=photo_size, height=photo_size)
            
            # Clean up temporary file
            os.remove(temp_img_path)
            
        except Exception as e:
            print(f"Error processing photo: {str(e)}")
            # Draw white circle as fallback
            c.setFillColorRGB(1, 1, 1)
            c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2, fill=1)
    else:
        # Draw white circle if no photo
        c.setFillColorRGB(1, 1, 1)
        c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2, fill=1)
    
    # Start content below photo circle
    y_position = height - photo_size - 60
    
    # Draw Name and Title
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(1, 1, 1)  # White color for text
    c.drawString(20, y_position, data['name'])  # Draw name
    y_position -= 25  # Move down for title
    c.setFont("Helvetica", 16)
    c.drawString(20, y_position, data['title'])  # Draw title
    y_position -= 40  # Additional space before About Me section

    # About me section
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(20, y_position, "About me")
    y_position -= 25
    
    # About text with wrapping
    y_position = wrap_text(data['about'], sidebar_width - 40, c, 20, y_position, "Helvetica", 10)
    
    # Contact section
    y_position -= 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y_position, "Contact")
    y_position -= 25
    
    # Contact details with wrapping
    c.setFont("Helvetica", 10)
    y_position = wrap_text(data['phone'], sidebar_width - 40, c, 20, y_position)
    y_position = wrap_text(data['email'], sidebar_width - 40, c, 20, y_position)
    y_position = wrap_text(data['address'], sidebar_width - 40, c, 20, y_position)
    
    # Expertise section
    y_position -= 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y_position, "Expertise")
    y_position -= 25
    
    # Draw skill bars
    c.setFont("Helvetica", 10)
    for name, level in zip(data['skill_names'], data['skill_levels']):
        y_position = wrap_text(name, sidebar_width - 40, c, 20, y_position)
        # Draw skill bar background
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.rect(20, y_position - 10, 80, 5, fill=1)
        # Draw skill level
        c.setFillColorRGB(1, 1, 1)
        level_width = (float(level) / 100) * 80
        c.rect(20, y_position - 10, level_width, 5, fill=1)
        y_position -= 25

    # Main content area (right side)
    right_margin = sidebar_width + 40  # Adjusted margin
    main_y_position = height - name_section_height - 60  # Start below black header
    right_width = width - right_margin - 40  # Adjusted width for content
    
    # Education section in white area
    c.setFillColorRGB(0, 0, 0)  # Black text
    c.setFont("Helvetica-Bold", 18)
    c.drawString(right_margin, main_y_position, "Education")
    main_y_position -= 30
    
    # Education entries with adjusted wrapping
    for i in range(len(data['edu_years'])):
        # Timeline dot
        c.circle(right_margin - 15, main_y_position + 5, 3, fill=1)
        
        c.setFont("Helvetica-Bold", 12)
        main_y_position = wrap_text_with_limit(data['edu_years'][i], right_width, c, right_margin, main_y_position, "Helvetica-Bold", 12)
        c.setFont("Helvetica", 10)
        main_y_position = wrap_text_with_limit(data['edu_school'][i], right_width, c, right_margin, main_y_position)
        main_y_position = wrap_text_with_limit(data['edu_location'][i], right_width, c, right_margin, main_y_position)
        main_y_position -= 25  # Increased spacing between entries

    # Experience section in white area
    main_y_position -= 30  # Extra space before Experience section
    c.setFont("Helvetica-Bold", 18)
    c.drawString(right_margin, main_y_position, "Experience")
    main_y_position -= 30
    
    # Experience entries with adjusted wrapping
    for i in range(len(data['exp_years'])):
        # Timeline dot
        c.circle(right_margin - 15, main_y_position + 5, 3, fill=1)
        
        c.setFont("Helvetica-Bold", 12)
        main_y_position = wrap_text_with_limit(data['exp_years'][i], right_width, c, right_margin, main_y_position, "Helvetica-Bold", 12)
        c.setFont("Helvetica", 10)
        main_y_position = wrap_text_with_limit(data['exp_position'][i], right_width, c, right_margin, main_y_position)
        main_y_position = wrap_text_with_limit(data['exp_description'][i], right_width, c, right_margin, main_y_position)
        main_y_position -= 25  # Increased spacing between entries

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return render_template_string(template)

@app.route('/generate', methods=['POST'])
def generate_pdf():
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
        
        photo = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                # Read the image directly into memory
                photo = BytesIO(file.read())
                print("Photo loaded successfully")  # Debug print

        pdf = create_pdf(data, photo)
        
        return send_file(
            pdf,
            download_name='resume.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return f"An error occurred while generating the PDF: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True) 