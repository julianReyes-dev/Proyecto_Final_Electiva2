import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import random
import string
from io import BytesIO
import base64

def allowed_file(filename, extensions=None):
    if extensions is None:
        extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def save_uploaded_file(file, upload_folder):
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Generate a random filename to prevent conflicts
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    filename = secure_filename(file.filename)
    filename = f"{random_str}_{filename}"
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Resize image if needed
    try:
        img = Image.open(filepath)
        if img.size[0] > 500 or img.size[1] > 500:
            img.thumbnail((500, 500))
            img.save(filepath)
    except Exception as e:
        print(f"Error processing image: {str(e)}")
    
    return filename

def generate_avatar(name, size=200):
    # Create a simple avatar with initials
    bg_color = (
        random.randint(100, 200),
        random.randint(100, 200),
        random.randint(100, 200)
    )
    
    # Get initials
    initials = ''.join([part[0].upper() for part in name.split()[:2]])
    if not initials:
        initials = 'AV'
    
    # Create image
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", size//2)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position
    text_width, text_height = draw.textsize(initials, font=font)
    position = ((size - text_width) // 2, (size - text_height) // 2)
    
    # Draw text
    draw.text(position, initials, fill=(255, 255, 255), font=font)
    
    # Save to bytes
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate filename
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    filename = f"avatar_{random_str}.png"
    
    # Save to file if needed
    filepath = os.path.join('static', 'avatars', filename)
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))
    
    with open(filepath, 'wb') as f:
        f.write(buffered.getvalue())
    
    return filename