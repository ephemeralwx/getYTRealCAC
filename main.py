from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import os
import openai  # Import the openai library

app = Flask(__name__)

# Constants
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY  # Set the API key

@app.route('/get_transcript', methods=['GET'])
def get_transcript():
    youtube_url = request.args.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'youtube_url is required'}), 400

    try:
        transcript_text = fetch_transcript(youtube_url)
        return jsonify({'transcript': transcript_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_summary', methods=['GET'])
def get_summary_from_youtube_url():
    youtube_url = request.args.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'youtube_url is required'}), 400

    try:
        transcript_text = fetch_transcript(youtube_url)
        prompt_text = transcript_text + "\n\nGenerate a summary for the text displayed above in less than 1350 characters."
        response = call_openai_api(prompt_text, max_tokens=300)
        return jsonify({'summary': response.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_howto_guide', methods=['GET'])
def get_howto_guide():
    youtube_url = request.args.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'youtube_url is required'}), 400

    try:
        transcript_text = fetch_transcript(youtube_url)
        prompt_text = transcript_text + "\n\nGenerate a friendly How-To step-by-step guide based on the text displayed above in less than 1350 characters. Make sure to number the steps."
        response = call_openai_api(prompt_text, max_tokens=300)
        return jsonify({'howto_guide': response.strip()})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ask_question', methods=['GET'])
def ask_question():
    youtube_url = request.args.get('youtube_url')
    question = request.args.get('question')

    if not youtube_url or not question:
        return jsonify({'error': 'Both youtube_url and question parameters are required'}), 400

    try:
        transcript_text = fetch_transcript(youtube_url)  # Fetch the transcript from the YouTube URL
        prompt = f"Given the following text: {transcript_text}, answer this question: {question}"
        response = call_openai_api(prompt, max_tokens=350)  # Adjust max_tokens as needed
        return jsonify({'answer': response.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def fetch_transcript(youtube_url):
    video_id = youtube_url.split('v=')[-1].split('&')[0]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = ' '.join([entry['text'] for entry in transcript])

    # Limiting the transcript to 10240 characters
    return transcript_text[:10240]

def call_openai_api(prompt, max_tokens):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=max_tokens
    )

    # Check if the response was successful
    if response['choices']:  # Check if choices are in the response
        return response['choices'][0]['message']['content'].strip()  # Extract and return the generated text
    else:
        raise Exception("OpenAI API error: {}".format(response['error']['message']))  # Handle any errors

if __name__ == '__main__':
    app.run(debug=True)
