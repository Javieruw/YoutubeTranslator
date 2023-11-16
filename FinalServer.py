from flask import Flask, request, jsonify
import whisper
from pytube import YouTube
import moviepy.editor as mp
import os

app = Flask(__name__)

@app.route('/process_string', methods=['POST'])
def process_string():
    data = request.json
    input_string = data['input']

    # Process the string here (this example just echoes it back)
    yt = YouTube(input_string)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download()

    # Saving the file as MP3
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    clip = mp.AudioFileClip(out_file)
    clip.write_audiofile(new_file)

    # Optionally, remove the original download (MP4 file)
    os.remove(out_file)

    model = whisper.load_model("base")
    print("transcription on the wawy")
    result = model.transcribe(base + ".mp3")

    return jsonify({"output": result["text"]})

    os.remove(new_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
