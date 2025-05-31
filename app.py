import os
import uuid
import logging
from flask import Flask, jsonify, request, render_template
from utils import get_owner_details, extract_number_plate  # Your updated function must accept reader param
from easyocr import Reader

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load easyocr Reader ONCE globally
reader = Reader(['en'])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "OK"})

@app.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'no image'}), 400
        file = request.files['image']

        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Call extract_number_plate with the global reader
        number_plate = extract_number_plate(filepath, reader=reader)

        # Delete uploaded file after processing
        os.remove(filepath)

        if not number_plate:
            return jsonify({'error': "number plate not found"}), 404

        owner = get_owner_details(number_plate)
        if owner:
            return jsonify({'number_plate': number_plate, 'owner': owner[0], 'phone': owner[1], 'address': owner[2]})
        else:
            return jsonify({'number_plate': number_plate, 'message': "no owner found in DB"})

    except Exception as e:
        logging.error(f"Error in /upload-image: {e}")
        return jsonify({'error': 'internal server error'}), 500

@app.route('/check-number', methods=['POST'])
def check_number():
    try:
        data = request.get_json()
        number = data.get("number_plate")
        if not number:
            return jsonify({"error": "number plate not provided"}), 400

        owner = get_owner_details(number)
        if owner:
            return jsonify({"number_plate": number, "owner": owner[0], "phone_number": owner[1], 'address': owner[2]})
        else:
            return jsonify({'number_plate': number, "message": "no owner found in db"})

    except Exception as e:
        logging.error(f"Error in /check-number: {e}")
        return jsonify({'error': 'internal server error'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
