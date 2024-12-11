import threading
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import time
from waitress import serve
from pyngrok import ngrok

# Set the ngrok authentication token
ngrok.set_auth_token("2q4gYvGblzBb3eszmA3mnz2cKYO_48nuEhYayw5unC44B9Yzx")

# Create the Flask app
app = Flask(__name__)

# Folder to save downloaded videos
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Folder to serve the HTML file (index.html)
STATIC_FOLDER = os.getcwd()  # Pointing to the root of the project folder where index.html is

# Dictionary to store download status
download_status = {}

# Function to download and optionally convert videos
def download_and_convert_video(url, quality='best', convert_to=None, download_id=None):
    """
    Download video and optionally convert to another format (e.g., MP3).
    
    :param url: URL of the video to download
    :param quality: Video quality (e.g., 'best', 'worst')
    :param convert_to: Format to convert the video to (e.g., 'mp3' for audio)
    :param download_id: ID to track the download status
    :return: Path to the downloaded and/or converted file
    """
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),  # Save video with title
        'format': quality,  # Download the best quality
    }

    # If conversion is requested (e.g., to MP3), add FFmpeg postprocessor
    if convert_to:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegAudio',  # Use FFmpeg for audio conversion
            'preferredcodec': convert_to,  # Set the conversion codec (e.g., 'mp3')
            'preferredquality': '192',  # Quality for audio (192kbps)
        }]

    try:
        # Update the download status as "In Progress"
        download_status[download_id] = 'In Progress'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)  # Download the video
            # Return the path to the downloaded and possibly converted file
            filename = f"{info_dict['title']}.{convert_to if convert_to else info_dict['ext']}"
            download_status[download_id] = 'Completed'
            return os.path.join(DOWNLOAD_FOLDER, filename)
    except Exception as e:
        download_status[download_id] = f"Error: {str(e)}"
        print(f"Error: {str(e)}")
        return None

# Function to handle download in a separate thread
def handle_download(url, quality, convert_to, download_id):
    video_path = download_and_convert_video(url, quality, convert_to, download_id)
    return video_path

# Route to render the homepage (serving index.html from the root folder)
@app.route('/')
def index():
    try:
        return send_from_directory(STATIC_FOLDER, 'index.html')
    except Exception as e:
        return jsonify({"error": f"Error serving the HTML: {str(e)}"}), 500

# Route to handle video download and optional conversion
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality', 'best')  # Default to 'best' quality
    convert_to = request.form.get('convert_to', None)  # Default to no conversion

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Generate a unique download ID to track status
        download_id = str(int(time.time()))  # Using timestamp as a simple ID
        download_status[download_id] = 'Started'

        # Run the download in a separate thread to avoid blocking Flask
        thread = threading.Thread(target=handle_download, args=(url, quality, convert_to, download_id))
        thread.start()

        return jsonify({
            'message': 'Download started. You can check the status later.',
            'download_id': download_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to check the download status
@app.route('/status/<download_id>', methods=['GET'])
def check_status(download_id):
    status = download_status.get(download_id, 'Invalid download ID')
    return jsonify({'status': status})

# Route to serve downloaded videos
@app.route('/downloaded/<filename>')
def serve_video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

# Run the app using a production-ready server (Waitress)
if __name__ == '__main__':
    # Set up ngrok tunnel
    public_url = ngrok.connect(5000)
    print(f'Ngrok tunnel "{public_url}" -> "http://127.0.0.1:5000"')
    
    # Using Waitress server for production environment
    serve(app, host='0.0.0.0', port=5000)  # Listen on all available IPs at port 5000
