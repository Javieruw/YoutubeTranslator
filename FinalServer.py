from flask import Flask, request, jsonify
import whisper
from pytube import YouTube
import moviepy.editor as mp
import os

app = Flask(__name__)

@app.route('/')
def index():
    token = secrets.token_hex(16)  # Generate a secure token
    return render_template('YoutubeTranslator.html', token=token)

@app.route('/process_string', methods=['POST'])
def process_string():

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
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
