import cv2
import numpy as np
import imutils
import easyocr
import mysql.connector
from mysql.connector import errorcode,connection


# Function to connect to the MySQL database
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
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None

#image processing and number extraction
def extract_number_plate(img_path):
    img = cv2.imread(img_path)
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

    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)

    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2]

    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)

    if result:
        text = result[0][-2]
        if text == "IND":
            text = result[1][-2]
        return text.replace(" ","")
    return None

# Look up in MySQL
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