import os
import logging
from flask import Blueprint, Flask, request, make_response, jsonify
import xml.etree.ElementTree as ET
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from common.configurations.app_config import AppConfig
from common.constants.vehicle_types import vehicle_types
from common.constants.vehicle_colors import vehicle_colors
from common.constants.vehicle_logos import vehicle_logos

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

@app.errorhandler(RequestEntityTooLarge)
def too_large(e):
    return make_response(jsonify(message="File is too large"), 413)


@app.route("/", methods=["POST"])
def handle_post():
    logging.info("Endpoint is called...")

    xml_data = request.data.decode("utf-8")
    logging.info(f"Received XML data: {xml_data}")

    root = ET.fromstring(xml_data)

    dateTime = datetime.fromisoformat(root.find(".//{http://www.isapi.org/ver20/XMLSchema}dateTime").text)
    licensePlate = root.find(".//{http://www.isapi.org/ver20/XMLSchema}licensePlate").text
    plateType = root.find(".//{http://www.isapi.org/ver20/XMLSchema}plateType").text
    plateColor = root.find(".//{http://www.isapi.org/ver20/XMLSchema}plateColor").text
    speedLimit = root.find(".//{http://www.isapi.org/ver20/XMLSchema}speedLimit").text

    vehicle_info = root.find(".//{http://www.isapi.org/ver20/XMLSchema}vehicleInfo")
    if vehicle_info is not None:
        vehicle_type = vehicle_types[int(vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}vehicleType").text)]
        vehicle_color = vehicle_colors[vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}color").text]
        vehicle_speed = int(vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}speed").text)
        vehicle_logo_recog = vehicle_logos[
            int(vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}vehicleLogoRecog").text)
        ]
        vehicle_sub_logo_recog = vehicle_logos[
            int(vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}vehicleSubLogoRecog").text)
        ]  # can be a mistake in here, because, vehicle wasn't written correctly
        vehicle_model = int(
            vehicle_info.find(".//{http://www.isapi.org/ver20/XMLSchema}vehicleModel").text
        )  # can be a mistake in here, because, vehicle wasn't written correctly
    else:
        vehicle_type = None
        vehicle_color = None
        vehicle_speed = None
        vehicle_logo_recog = None
        vehicle_sub_logo_recog = None
        vehicle_model = None

    # Process images
    license_plate_picture = request.files.get("licensePlatePicture.jpg")
    detection_picture = request.files.get("detectionPicture.jpg")

    if license_plate_picture or detection_picture:
        images_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{licensePlate}/{dateTime.strftime('%Y-%m-%d_%H-%M-%S')}")
        if not os.path.exists(images_folder_path):
            os.makedirs(images_folder_path)
            logging.info(f"Directory '{images_folder_path}' created successfully.")

    # Save images
    if license_plate_picture:
        try:
            filename = secure_filename(license_plate_picture.filename)
            license_plate_picture.save(os.path.join(images_folder_path, filename))
        except Exception as exception:
            logging.error('Error occured while license_plate_picture is saving.', exception)
    if detection_picture:
        try:
            filename = secure_filename(detection_picture.filename)
            detection_picture.save(os.path.join(images_folder_path, filename))
        except Exception as exception:
            logging.error('Error occured while detection_picture is saving.', exception)

    logging.info(
        f"Detected plate info:\ndateTime={dateTime}\nlicensePlate={licensePlate}\nplateType={plateType}\nplateColor={plateColor}\nspeedLimit={speedLimit}\nvehicle_type={vehicle_type}\nvehicle_color={vehicle_color}\nvehicle_speed={vehicle_speed}\nvehicle_logo_recog={vehicle_logo_recog}\nvehicle_sub_logo_recog={vehicle_sub_logo_recog}\nvehicle_model={vehicle_model}"
    )

    return "Data stored successfully"


if __name__ == "__main__":
    app_config = AppConfig()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = './detected_vehicles'
    app.run(debug=True, host=app_config.host, port=app_config.port)
