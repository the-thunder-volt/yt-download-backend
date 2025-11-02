from flask import Flask, request, send_file, jsonify
import subprocess
import tempfile
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data["url"]
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"video_{int(os.times()[4])}.mp4")

    command = ["yt-dlp", "-f", "bv*+ba/b", "-o", output_path, url]

    try:
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Download failed",
            "details": e.stderr.decode("utf-8", errors="ignore")
        }), 500

    if not os.path.exists(output_path):
        return jsonify({"error": "Output file not found"}), 500

    response = send_file(
        output_path,
        as_attachment=True,
        download_name="video.mp4",
        mimetype="video/mp4"
    )

    @response.call_on_close
    def cleanup():
        try:
            os.remove(output_path)
        except Exception:
            pass

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
