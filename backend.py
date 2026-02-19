from flask import Flask, request, jsonify, render_template
import os
import uuid
from predict_engine import decision_engine
from cloudant_db import save_to_database, get_real_images, client, DATABASE_NAME

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/posts")
def posts():
    return render_template("post.html")

@app.route("/predict", methods=["POST"])
def predict():

    try:

        if "file" not in request.files:
            return jsonify({
                "allowed": False,
                "message": "No file uploaded"
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "allowed": False,
                "message": "Empty filename"
            }), 400

        # Unique filename
        unique_name = str(uuid.uuid4()) + "_" + file.filename
        file_path = os.path.join(UPLOAD_FOLDER, unique_name)

        file.save(file_path)

        # Run model
        decision, confidence = decision_engine(file_path)

        label = 1 if decision == "REAL" else 0

        # Read image as base64 for Cloudant
        import base64

        with open(file_path, "rb") as img:
            image_data = base64.b64encode(img.read()).decode("utf-8")

        # Save to Cloudant
        save_to_database(
            filename=unique_name,
            label=label,
            confidence=confidence,
            image_data=image_data
        )

        # Remove temp file safely
        try:
            os.remove(file_path)
        except:
            pass

        # User response logic
        if label == 1:

            return jsonify({
                "decision": "REAL",
                "confidence": confidence,
                "allowed": True,
                "message": "Uploaded Successfully"
            })

        else:

            return jsonify({
                "decision": "FAKE",
                "confidence": confidence,
                "allowed": False,
                "message": "Upload Restricted – AI Generated Image"
            })

    except Exception as e:

        print("ERROR in /predict:", str(e))

        return jsonify({
            "allowed": False,
            "message": "Server error"
        }), 500
        
        
@app.route("/get_real_images")
def get_real_images():

    response = client.post_find(
        db=DATABASE_NAME,
        selector={"label": 1}
    ).get_result()

    return jsonify(response["docs"])





if __name__ == "__main__":
    app.run(debug=False)
