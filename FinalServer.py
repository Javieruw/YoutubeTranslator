from flask import Flask, request, jsonify, render_template
import whisper
from pytube import YouTube
import moviepy.editor as mp
import os
from celery import Celery

app = Flask(__name__)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = make_celery(app)

@celery.task
def process_video(input_string):
    print("Downloading YouTube video")
    yt = YouTube(input_string)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download()

    print("Converting to MP3")
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    clip = mp.AudioFileClip(out_file)
    clip.write_audiofile(new_file)

    print("Removing original MP4 file")
    os.remove(out_file)

    print("Loading Whisper model and transcribing")
    model = whisper.load_model("base")
    result = model.transcribe(new_file)

    print("Cleaning up MP3 file")
    os.remove(new_file)

    return result["text"]

@app.route('/')
def index():
    return render_template('YoutubeTranslator.html')

@app.route('/process_string', methods=['POST'])
def process_string():
    try:
        print("Received request for process_string")
        data = request.json
        input_string = data['input']

        # Start the Celery task
        task = process_video.delay(input_string)

        print("Task submitted to Celery")
        return jsonify({"task_id": task.id}), 202

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
