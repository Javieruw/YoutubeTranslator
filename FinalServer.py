from flask import Flask, request, jsonify
import whisper
from pytube import YouTube
import moviepy.editor as mp
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# @app.route('/process_string', methods=['POST'])
# def process_string():
#      # client_ip = request.remote_addr
#      # server_ip = '154.62.108.77'  # Replace with your server's IP address
#     #
#      # Check if the client IP matches the server IP
#     # if client_ip != server_ip:
#     #     return jsonify({"error": "Access denied"}), 403
#
#     data = request.json
#     input_string = data['input']
#
#     # Process the string here (this example just echoes it back)
#     yt = YouTube(input_string)
#     video = yt.streams.filter(only_audio=True).first()
#     out_file = video.download()
#
#     # Saving the file as MP3
#     base, ext = os.path.splitext(out_file)
#     new_file = base + '.mp3'
#     clip = mp.AudioFileClip(out_file)
#     clip.write_audiofile(new_file)
#
#     # Optionally, remove the original download (MP4 file)
#     os.remove(out_file)
#
#     model = whisper.load_model("base")
#     print("transcription on the way")
#     result = model.transcribe(base + ".mp3")
#     os.remove(new_file)
#
#     return jsonify({"output": result["text"]})
#
#
# if __name__ == '__main__':
#     app.run(debug=True)

@app.route('/process_string', methods=['POST'])
# def process_string():
#     client_ip = request.remote_addr
#     print(f"Client IP: {client_ip}")  # Debugging print statement

#     allowed_ip = '154.62.108.77'
#     if client_ip != allowed_ip:
#         return jsonify({"error": "Unauthorized access from IP: " + client_ip}), 403


    try:
        data = request.json
        input_string = data['input']

        yt = YouTube(input_string)
        video = yt.streams.filter(only_audio=True).first()
        out_file = video.download()

        # Saving the file as MP3
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        clip = mp.AudioFileClip(out_file)
        clip.write_audiofile(new_file)

        # Remove the original download (MP4 file)
        os.remove(out_file)

        # Load the model and transcribe
        model = whisper.load_model("base")
        result = model.transcribe(new_file)

        # Clean up the MP3 file
        os.remove(new_file)

        return jsonify({"output": result["text"]})

    except Exception as e:
        # Handle exceptions and return an error message
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, threaded=True)
