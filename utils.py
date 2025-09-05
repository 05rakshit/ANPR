import cv2
import numpy as np
import imutils
import easyocr
import mysql.connector
from mysql.connector import errorcode, connection
import os

# Initialize EasyOCR reader once globally (faster)
reader = easyocr.Reader(['en'], gpu=False)

# Connect to MySQL
def connect_to_database():
    try:
        cnx = connection.MySQLConnection(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "password"),
            host=os.environ.get("DB_HOST", "localhost"),
            database=os.environ.get("DB_NAME", "railway"),
            port=int(os.environ.get("DB_PORT", 3306))
        )
        return cnx
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# Extract number plate from image
def extract_number_plate(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(bfilter, 30, 200)

    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break

    if location is None:
        return None

    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)

    # Crop the plate region
    (x, y) = np.where(mask == 255)
    if len(x) == 0 or len(y) == 0:
        return None

    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    if x1 >= x2 or y1 >= y2:
        return None

    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]

    # OCR to read text
    result = reader.readtext(cropped_image)
    if result:
        # Pick the text with highest confidence
        result = sorted(result, key=lambda r: r[2], reverse=True)
        text = result[0][1].replace(" ", "")
        if text.upper() == "IND" and len(result) > 1:
            text = result[1][1].replace(" ", "")
        return text
    return None

# Get owner details from DB
def get_owner_details(number_plate):
    cnx = connect_to_database()
    if not cnx:
        return None

    cursor = cnx.cursor()
    try:
        cursor.execute(
            "SELECT owner_name, phone_number, address FROM vehicle_owner WHERE number_plate = %s",
            (number_plate,)
        )
        owner_info = cursor.fetchone()
        return owner_info
    finally:
        cursor.close()
        cnx.close()
