import os
import uuid
from flask import Flask, jsonify, request, render_template
from utils import get_owner_details, extract_number_plate

app = Flask(__name__)

# Folder to save uploaded images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty file name'}), 400

    # Save file with unique name to avoid collisions
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Extract number plate
    number_plate = extract_number_plate(filepath)

    # Remove file after processing
    os.remove(filepath)

    if not number_plate:
        return jsonify({'error': "Number plate not found"}), 404

    owner = get_owner_details(number_plate)
    if owner:
        return jsonify({
            'number_plate': number_plate,
            'owner': owner[0],
            'phone_number': owner[1],
            'address': owner[2]
        })
    else:
        return jsonify({'number_plate': number_plate, 'message': "No owner found in DB"})

@app.route('/check-number', methods=['POST'])
def check_number():
    data = request.get_json()
    if not data or 'number_plate' not in data:
        return jsonify({"error": "Number plate not provided"}), 400

    number = data['number_plate']
    owner = get_owner_details(number)

    if owner:
        return jsonify({
            "number_plate": number,
            "owner": owner[0],
            "phone_number": owner[1],
            "address": owner[2]
        })
    else:
        return jsonify({'number_plate': number, "message": "No owner found in DB"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
