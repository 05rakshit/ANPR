import os
import uuid
from flask import Flask, jsonify, request, render_template
from utils import get_owner_details, extract_number_plate

app = Flask(__name__)

# Temporary uploads folder
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/upload-image', methods=['POST'])
def upload_image():
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No image provided'}), 400

    # Unique filename
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    number_plate = extract_number_plate(filepath)
    os.remove(filepath)  # delete after processing

    if not number_plate:
        return jsonify({'error': 'Number plate not found'}), 404

    owner = get_owner_details(number_plate)
    if owner:
        return jsonify({
            'number_plate': number_plate,
            'owner': owner[0],
            'phone_number': owner[1],
            'address': owner[2]
        })
    else:
        return jsonify({
            'number_plate': number_plate,
            'message': 'No owner found in DB'
        })


@app.route('/check-number', methods=['POST'])
def check_number():
    data = request.get_json()
    number = data.get("number_plate")
    if not number:
        return jsonify({"error": "Number plate not provided"}), 400

    owner = get_owner_details(number)
    if owner:
        return jsonify({
            "number_plate": number,
            "owner": owner[0],
            "phone_number": owner[1],
            "address": owner[2]
        })
    else:
        return jsonify({
            'number_plate': number,
            "message": "No owner found in DB"
        })
