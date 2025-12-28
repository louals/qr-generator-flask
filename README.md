# QR Code Generator API

This is a simple **QR code generator API** built with Python and Flask.  
Users can send a URL and get a QR code image in response.

---

## Features

- Generate QR codes from any URL
- Returns PNG image
- Deployable on Render or any cloud server
- Easy to connect with frontend (React, Vue, etc.)

---

## Tech Stack

- Python 3
- Flask
- qrcode[pil] (Pillow for image handling)

---

## Usage

### 1. Run locally

```bash
# Activate venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
