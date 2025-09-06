import cv2
import easyocr
import re
import mysql.connector
from mysql.connector import connection

# Initialize EasyOCR reader once
reader = easyocr.Reader(['en'])

def connect_to_database():
    """
    Connect to your Railway MySQL database.
    """
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
        print("Database connection error:", err)
        return None


def clean_number_plate(text):
    """
    Cleans and validates the OCR extracted text to match Indian vehicle number plate format.
    """
    # Remove non-alphanumeric characters and convert to uppercase
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # Common OCR misreads correction
    corrections = {
        'O': '0',
        'I': '1',
        'Z': '2',
        'S': '5',
        'B': '8'
    }
    for k, v in corrections.items():
        text = text.replace(k, v)

    # Indian number plate regex
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'

    # If direct match → return
    if re.match(pattern, text):
        return text

    # If one extra char (like DL9CBE02585 → DL9CBE0258)
    if re.match(pattern, text[:-1]):
        return text[:-1]

    # If still not valid, return raw but corrected text
    return text


def extract_number_plate(image_path):
    """
    Extracts and cleans the number plate text from an image using EasyOCR.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image {image_path}")
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # OCR with EasyOCR
    results = reader.readtext(gray)

    # Loop over detections
    for (bbox, text, prob) in results:
        if prob > 0.3:  # confidence threshold
            plate = clean_number_plate(text)
            if len(plate) >= 8:  # avoid short junk results
                return plate
    return None


def get_owner_details(number_plate):
    """
    Fetch owner details from the DB given a valid number plate.
    """
    cnx = connect_to_database()
    if cnx:
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT owner_name, phone_number, address FROM vehicle_owner WHERE number_plate = %s",
            (number_plate,)
        )
        owner_info = cursor.fetchone()
        cursor.close()
        cnx.close()
        return owner_info
    return None
