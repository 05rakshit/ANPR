from PIL import Image, ExifTags
import cv2
import numpy as np
import easyocr
import re
import mysql.connector
from mysql.connector import connection

# Initialize EasyOCR once
reader = easyocr.Reader(['en'], gpu=False)


def connect_to_database():
    """Connect to Railway MySQL database."""
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
        print("[DB ERROR]", err)
        return None


def clean_number_plate(text: str) -> str:
    """Cleans OCR output into valid Indian number plate format."""
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # Split into prefix (state code + RTO, usually first 4 chars) and rest
    prefix, rest = text[:4], text[4:]

    # Apply corrections ONLY to numeric part
    corrections = {
        'O': '0',
        'I': '1',
        'Z': '2',
        'S': '5',
        'B': '8',
        'G': '6',
        'Q': '0'
    }
    cleaned_rest = "".join(corrections.get(ch, ch) for ch in rest)
    text = prefix + cleaned_rest

    # Indian number plate regex
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'

    # Handle cases
    if len(text) > 10 and re.match(pattern, text[1:]):
        return text[1:]  # Extra leading char

    if re.match(pattern, text):
        return text  # Valid plate

    if re.match(pattern, text[:-1]):
        return text[:-1]  # Off-by-one char at end

    return text


def extract_number_plate(img_path: str):
    """Extracts number plate text from an image using EasyOCR."""
    # Handle EXIF rotation
    pil_img = Image.open(img_path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = pil_img._getexif()
        if exif:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                pil_img = pil_img.rotate(180, expand=True)
            elif orientation_value == 6:
                pil_img = pil_img.rotate(270, expand=True)
            elif orientation_value == 8:
                pil_img = pil_img.rotate(90, expand=True)
    except Exception:
        pass

    # Convert to OpenCV
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Resize if image is too wide
    if img.shape[1] > 800:
        scale = 800 / img.shape[1]
        img = cv2.resize(img, (800, int(img.shape[0] * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Preprocessing
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    edged = cv2.Canny(gray, 30, 200)

    # Find contours
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(keypoints[0], key=cv2.contourArea, reverse=True)[:15]

    plate_img = None
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        if 2 < aspect_ratio < 6:  # Plates are rectangular
            if 1000 < cv2.contourArea(contour) < 15000:
                plate_img = gray[y:y+h, x:x+w]
                break

    # Fallback to full image if no contour match
    if plate_img is None:
        plate_img = gray

    # OCR with EasyOCR
    results = reader.readtext(plate_img)

    # Filter confident results
    results = [r for r in results if r[-1] > 0.3]

    if results:
        best_result = max(results, key=lambda r: r[-1])
        return clean_number_plate(best_result[1])
    return None


def get_owner_details(number_plate: str):
    """Fetch owner details from DB for given number plate."""
    try:
        cnx = connect_to_database()
        if not cnx:
            return None
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT owner_name, phone_number, address FROM vehicle_owner WHERE number_plate = %s",
            (number_plate,)
        )
        owner_info = cursor.fetchone()
        cursor.close()
        cnx.close()
        return owner_info
    except mysql.connector.Error as err:
        print("[DB QUERY ERROR]", err)
        return None
