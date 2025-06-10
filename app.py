import numpy as np
from flask import Flask,jsonify, request, render_template
import os
from utils import get_owner_details, extract_number_plate

app=Flask(__name__)
UPLOAD_FOLDER='uploads'
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload-image',methods=['POST','GET'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error':'no image'}),400
    file=request.files['image']
    filepath=os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    number_plate=extract_number_plate(filepath)
    if not number_plate:
        return jsonify({'error':"number pate not foudn"}),404
    
    owner=get_owner_details(number_plate)
    if owner:
        return jsonify({'number_plate':number_plate, 'owner':owner[0], "phone_number":owner[1], 'address':owner[2]})
    
    else:
        return jsonify({'number_plate':number_plate, 'message':"no onwer found in DB"})
    

@app.route('/check-number',methods=['POST','GET'])
def check_number():
    data=request.get_json()
    number=data.get("number_plate")
    if not number:
        return jsonify({"error":"number plate not provided"}),400
    
    owner= get_owner_details(number)
    if owner:
        return jsonify({"number_plate":number, "owner":owner[0], "phone_number":owner[1], 'address':owner[2]})
    
    else:
        return jsonify({'number_plate':number, "message":"no onwer found in db"})
    
if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))  # use Render's assigned port or default 5000
    app.run(host="0.0.0.0", port=port)