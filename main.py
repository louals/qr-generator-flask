import os
from flask import Flask, request, send_file
import qrcode
import uuid

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return {"message": "QR Code API is running"}, 200

@app.route("/generate", methods=["POST"])
def generate_qr():
    data = request.json
    url = data.get("url")

    if not url:
        return {"error": "URL is required"}, 400

    # Generate QR
    qr_img = qrcode.make(url)

    # Save with unique name
    filename = f"{uuid.uuid4()}.png"
    qr_img.save(filename)

    return send_file(filename, mimetype="image/png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
