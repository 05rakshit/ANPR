from PIL import Image, ExifTags
import cv2
import numpy as np
import easyocr
import mysql.connector
from mysql.connector import connection

# Initialize EasyOCR once (faster performance)
reader = easyocr.Reader(['en'], gpu=False)

def connect_to_database():
    try:
        cnx = connection.MySQLConnection(
            user='root', 
            password='QHdpjQYeAqWdLwnuIQPcwPwrHBcCwJFY', 
            host='mainline.proxy.rlwy.net', 
            database='railway', 
            port='55270'
        )
        return cnx
    except mysql.connector.Error as err:
        print(err)
        return None


def extract_number_plate(img_path):
    # Open image with PIL to handle EXIF rotation
    pil_img = Image.open(img_path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = pil_img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                pil_img = pil_img.rotate(180, expand=True)
            elif orientation_value == 6:
                pil_img = pil_img.rotate(270, expand=True)
            elif orientation_value == 8:
                pil_img = pil_img.rotate(90, expand=True)
    except:
        pass

    # Convert to OpenCV
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # ✅ Resize main image (fixed width 800px for consistency)
    img = cv2.resize(img, (800, int(img.shape[0] * 800 / img.shape[1])))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise & enhance contrast
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Edge detection
    edged = cv2.Canny(gray, 30, 200)

    # Find contours
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(keypoints[0], key=cv2.contourArea, reverse=True)[:15]

    plate_img = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:  # likely number plate shape
            x, y, w, h = cv2.boundingRect(contour)
            plate_img = gray[y:y+h, x:x+w]
            break

    # If no plate detected, fallback to full image
    if plate_img is None:
        plate_img = gray

    # ✅ Resize plate region for better OCR accuracy
    plate_img = cv2.resize(plate_img, (400, int(plate_img.shape[0] * 400 / plate_img.shape[1])))

    # OCR with EasyOCR
    results = reader.readtext(plate_img)

    if results:
        # Take best result with highest confidence
        best_result = max(results, key=lambda r: r[-1])
        text = best_result[1].upper().replace(" ", "").replace("-", "")
        return text
    return None


def get_owner_details(number_plate):
    cnx = connect_to_database()
    if cnx:
        cursor = cnx.cursor()
        cursor.execute("SELECT owner_name, phone_number, address FROM vehicle_owner WHERE number_plate = %s", (number_plate,))
        owner_info = cursor.fetchone()
        cursor.close()
        cnx.close()
        return owner_info
    return None
