from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from datetime import datetime
import base64
import os

# =============================
# IBM Cloudant Credentials
# =============================

API_KEY = "jP2nJBdE3VVg-H14-aGNUU5Trj7Dkzq6T15KYx9gaaki"
URL = "https://ce12612f-8009-4c78-ad03-087c1b2fa6d5-bluemix.cloudantnosqldb.appdomain.cloud"
DATABASE_NAME = "image_verification"

# =============================
# Connect to Cloudant
# =============================

authenticator = IAMAuthenticator(API_KEY)

client = CloudantV1(authenticator=authenticator)
client.set_service_url(URL)

print("Cloudant Connected Successfully")

# =============================
# Save Image + Metadata
# =============================

def save_to_database(filename, label, confidence, image_data):

    data = {

        "filename": filename,

        "label": label,

        "confidence": confidence,

        "image_data": image_data,

        "timestamp": datetime.now().isoformat()

    }

    response = client.post_document(
        db=DATABASE_NAME,
        document=data
    ).get_result()

    print("Saved to Cloudant:", response["id"])



# =============================
# Get ONLY REAL Images
# =============================

def get_real_images():
    response = client.post_find(
        db=DATABASE_NAME,
        selector={"label": 1}
    ).get_result()

    return response["docs"]

