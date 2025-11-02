from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os

app = Flask(__name__)

# ✅ Allow all origins (you can later restrict to your frontend domain if needed)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    # ===============================
    # 1️⃣ Handle CORS preflight (OPTIONS)
    # ===============================
    if request.method == "OPTIONS":
        response = jsonify({"status": "OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    # ===============================
    # 2️⃣ Parse JSON request
    # ===============================
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data["url"]

    # ===============================
    # 3️⃣ Prepare temporary output file
    # ===============================
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"video_{int(os.times()[4])}.mp4")

    # ===============================
    # 4️⃣ Run yt-dlp to download video
    # ===============================
    command = [
        "yt-dlp",
        "-f", "bv*+ba/b",
        "-o", output_path,
        url
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Download failed",
            "details": e.stderr.decode("utf-8", errors="ignore")
        }), 500

    # ===============================
    # 5️⃣ Check if file exists
    # ===============================
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file not found"}), 500

    # ===============================
    # 6️⃣ Send file to client
    # ===============================
    response = send_file(
        output_path,
        as_attachment=True,
        download_name="video.mp4",
        mimetype="video/mp4"
    )
    response.headers.add("Access-Control-Allow-Origin", "*")

    # ===============================
    # 7️⃣ Cleanup temporary file
    # ===============================
    @response.call_on_close
    def cleanup():
        try:
            os.remove(output_path)
        except Exception:
            pass

    return response


# ===============================
# 8️⃣ Run locally or on Render
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
