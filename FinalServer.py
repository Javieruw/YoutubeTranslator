from flask import Flask, request, jsonify, render_template
import whisper
import yt_dlp as ytdlp
import moviepy.editor as mp
import os
from celery import Celery
from flask import url_for

app = Flask(__name__)

# Celery configuration
app.config['broker_url'] = 'redis://redis:6379/0'
app.config['result_backend'] = 'redis://redis:6379/0'
app.config['worker_concurrency'] = int('1')
app.config['task_acks_late'] = True
app.config['worker_prefetch_multiplier'] = int('1')

# Initialize Celery
celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)

@celery.task(time_limit=2000)
def process_video(input_string):
    try:
        print("Downloading YouTube video")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/app/%(title)s.%(ext)s',
        }
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(input_string, download=True)
            file_name = ydl.prepare_filename(info_dict)

        # Convert the downloaded video to MP3
        print("Converting to MP3")
        base, ext = os.path.splitext(file_name)
        new_file = base + '.mp3'
        clip = mp.AudioFileClip(file_name)
        clip.write_audiofile(new_file)

        # Remove the original file
        if os.path.exists(file_name):
            print(f"Removing original file: {file_name}")
            os.remove(file_name)

        # Load Whisper model and transcribe the audio
        print("Loading Whisper model and transcribing")
        model = whisper.load_model("base")
        result = model.transcribe(new_file)

        # Clean up MP3 file after transcription
        print("Cleaning up MP3 file")
        os.remove(new_file)

        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"],
                    "start": word_info["start"],
                    "end": word_info["end"]
                })

        return result["text"]

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}

@app.route('/')
def index():
    icon_url = url_for('static', filename='jp_icon.ico')
    return render_template('YoutubeTranslator.html')

@app.route('/process_string', methods=['POST'])
def process_string():
    try:
        print("Received request for process_string")
        data = request.json
        input_string = data['input']

        # Start the Celery task if worker is available:
        task = process_video.delay(input_string)

        print("Task submitted to Celery")
        return jsonify({"task_id": task.id}), 202

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_task_result/<task_id>', methods=['GET'])
def get_task_result(task_id):
    task = process_video.AsyncResult(task_id)
    if task.state == 'PENDING':
        # Task is still processing
        response = {
            'state': task.state,
            'status': 'Task is still processing'
        }
    elif task.state != 'FAILURE':
        # Task completed successfully
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        # Something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info)  # Exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5060, debug=False, threaded=True)
