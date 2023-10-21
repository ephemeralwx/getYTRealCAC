from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import os
import openai  # Import the openai library instead of requests

app = Flask(__name__)

# Constants
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

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
        prompt_text = transcript_text + "\n\nGenerate a summary for the text displayed above."
        response = call_openai_api(prompt_text, max_tokens=150)
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
        prompt_text = transcript_text + "\n\nGenerate a friendly How-To step-by-step guide based on the text displayed above. Make sure to number the steps."
        response = call_openai_api(prompt_text, max_tokens=300)
        return jsonify({'howto_guide': response.strip()})
    except Exception as e:
        return jsonify({'error': str(e)})

def fetch_transcript(youtube_url):
    video_id = youtube_url.split('v=')[-1].split('&')[0]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = ' '.join([entry['text'] for entry in transcript])

    # Limiting the transcript to 10240 characters
    return transcript_text[:10240]

def call_openai_api(prompt, max_tokens):
    openai.api_key = OPENAI_API_KEY  # Set the API key
    response = openai.Completion.create(  # Use openai.Completion.create instead of requests.post
        engine="gpt-4",  # Update the engine to gpt-4
        prompt=prompt,
        max_tokens=max_tokens
    )

    # Check if the response was successful
    if response['choices']:  # Check if choices are in the response
        return response['choices'][0]['text'].strip()  # Extract and return the generated text
    else:
        raise Exception("OpenAI API error: {}".format(response['error']['message']))  # Handle any errors

if __name__ == '__main__':
    app.run(debug=True)
