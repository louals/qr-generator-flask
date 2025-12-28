import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image
import uuid
import io
import traceback

app = Flask(__name__)

# Configure CORS - allow all origins for development
# In production, you should specify allowed origins
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:5500"]}})

# For development, you can also allow all origins:
# CORS(app)

# Error correction levels mapping
ERROR_CORRECTION_MAP = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H
}

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/", methods=["GET"])
def home():
    """API home endpoint"""
    return {
        "message": "QR Code Generator API",
        "version": "1.0.0",
        "endpoints": {
            "/generate": "Generate QR code (GET or POST)",
            "/health": "API health check"
        }
    }, 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}, 200

@app.route("/generate", methods=["GET", "POST", "OPTIONS"])
def generate_qr():
    """Generate QR code from URL with customization options"""
    try:
        # Handle preflight request
        if request.method == "OPTIONS":
            return "", 200
        
        # Get parameters from GET or POST request
        if request.method == "GET":
            url = request.args.get("url")
            size = request.args.get("size", "300")
            color = request.args.get("color", "000000")
            bg_color = request.args.get("bg_color", "ffffff")
            margin = request.args.get("margin", "4")
            error_correction = request.args.get("error_correction", "M")
            fill_style = request.args.get("fill_style", "square")  # square or circle
            
        else:  # POST request
            data = request.get_json() if request.is_json else request.form
            
            if not data:
                return jsonify({"error": "Invalid request format. Use JSON or form data"}), 400
            
            url = data.get("url")
            size = data.get("size", "300")
            color = data.get("color", "000000")
            bg_color = data.get("bg_color", "ffffff")
            margin = data.get("margin", "4")
            error_correction = data.get("error_correction", "M")
            fill_style = data.get("fill_style", "square")

        # Validate URL
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'sms:')):
            return jsonify({"error": "URL must start with http://, https://, mailto:, tel:, or sms:"}), 400

        # Convert parameters to appropriate types
        try:
            size = int(size)
            if size < 100 or size > 1000:
                return jsonify({"error": "Size must be between 100 and 1000 pixels"}), 400
        except ValueError:
            return jsonify({"error": "Size must be a number"}), 400

        try:
            margin = int(margin)
            if margin < 0 or margin > 20:
                return jsonify({"error": "Margin must be between 0 and 20"}), 400
        except ValueError:
            return jsonify({"error": "Margin must be a number"}), 400

        # Validate and convert colors
        def validate_color(color_str, param_name):
            if len(color_str) == 6:
                try:
                    int(color_str, 16)
                    return color_str
                except ValueError:
                    pass
            elif len(color_str) == 7 and color_str.startswith('#'):
                try:
                    int(color_str[1:], 16)
                    return color_str[1:]
                except ValueError:
                    pass
            raise ValueError(f"Invalid {param_name} format")

        try:
            color = validate_color(color, "color")
            bg_color = validate_color(bg_color, "background color")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Validate error correction level
        error_correction = error_correction.upper()
        if error_correction not in ERROR_CORRECTION_MAP:
            return jsonify({"error": "Error correction must be L, M, Q, or H"}), 400

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECTION_MAP[error_correction],
            box_size=10,
            border=margin,
        )
        
        qr.add_data(url)
        qr.make(fit=True)

        # Create QR code image with custom colors
        qr_img = qr.make_image(
            fill_color=f"#{color}",
            back_color=f"#{bg_color}",
            image_factory=None
        )

        # Resize image if requested
        if size != qr_img.size[0]:
            qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

        # Convert PIL Image to bytes
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG', quality=95)
        img_io.seek(0)

        # Generate filename
        filename = f"qr_{uuid.uuid4().hex[:8]}.png"

        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to generate QR code: {str(e)}"}), 500

@app.route("/generate/v2", methods=["POST"])
def generate_qr_v2():
    """Enhanced QR code generation with logo support"""
    try:
        data = request.form
        url = data.get("url")
        
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400

        # Get customization parameters
        size = int(data.get("size", 300))
        color = data.get("color", "000000")
        bg_color = data.get("bg_color", "ffffff")
        
        # Handle logo upload if provided
        logo_img = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file.filename != '':
                try:
                    logo_img = Image.open(logo_file.stream)
                    # Convert to RGBA if necessary
                    if logo_img.mode != 'RGBA':
                        logo_img = logo_img.convert('RGBA')
                except Exception as e:
                    return jsonify({"error": f"Invalid logo image: {str(e)}"}), 400

        # Generate base QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_H,  # Higher error correction for logos
            box_size=10,
            border=4,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(
            fill_color=f"#{color}",
            back_color=f"#{bg_color}"
        ).convert('RGBA')

        # Add logo if provided
        if logo_img:
            # Calculate logo size (20% of QR code size)
            logo_size = min(qr_img.size) // 5
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position to center the logo
            pos = ((qr_img.size[0] - logo_img.size[0]) // 2,
                   (qr_img.size[1] - logo_img.size[1]) // 2)
            
            # Create a mask from the logo's alpha channel
            mask = logo_img.split()[3] if len(logo_img.split()) == 4 else None
            
            # Paste logo onto QR code
            qr_img.paste(logo_img, pos, mask=mask)

        # Resize if requested
        if size != qr_img.size[0]:
            qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to bytes
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG', quality=95)
        img_io.seek(0)

        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"qr_with_logo_{uuid.uuid4().hex[:8]}.png"
        )

    except Exception as e:
        print(f"Error generating QR code with logo: {str(e)}")
        return jsonify({"error": f"Failed to generate QR code: {str(e)}"}), 500

@app.route("/batch", methods=["POST"])
def generate_batch_qr():
    """Generate multiple QR codes in batch"""
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({"error": "List of URLs is required"}), 400
        
        urls = data['urls']
        if not isinstance(urls, list) or len(urls) > 50:
            return jsonify({"error": "Provide up to 50 URLs in a list"}), 400
        
        # Get common parameters
        size = int(data.get("size", 300))
        color = data.get("color", "000000")
        
        results = []
        
        for url in urls:
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=ERROR_CORRECT_M,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url)
                qr.make(fit=True)
                
                qr_img = qr.make_image(
                    fill_color=f"#{color}",
                    back_color="#ffffff"
                )
                
                if size != qr_img.size[0]:
                    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
                
                img_io = io.BytesIO()
                qr_img.save(img_io, 'PNG')
                img_io.seek(0)
                
                # Store as base64 for batch response
                import base64
                img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
                
                results.append({
                    "url": url,
                    "qr_code": img_base64,
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "status": "error"
                })
        
        return jsonify({
            "total": len(urls),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Batch generation failed: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Development mode settings
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"Starting QR Generator API on port {port}")
    print(f"Debug mode: {debug}")
    print(f"CORS enabled for localhost and common development ports")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )