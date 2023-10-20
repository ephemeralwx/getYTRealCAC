from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import os

app = Flask(__name__)

# Fetch the OpenAI API key from an environment variable
openai.api_key = os.environ.get('OPENAI_API_KEY')

@app.route('/get_summary', methods=['GET'])
def get_summary_from_youtube_url():
    youtube_url = request.args.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'youtube_url is required'}), 400

    try:
        transcript_text = fetch_transcript(youtube_url)
        prompt_text = transcript_text + "\n\nGenerate a summary for the text displayed above."
        response = openai.Completion.create(engine="davinci", prompt=prompt_text, max_tokens=150)
        return jsonify({'summary': response.choices[0].text.strip()})

    except YouTubeTranscriptApi.CouldNotRetrieveTranscript:
        return jsonify({'error': 'Could not retrieve the transcript for the provided YouTube video.'}), 400
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
        response = openai.Completion.create(engine="davinci", prompt=prompt_text, max_tokens=300)
        return jsonify({'howto_guide': response.choices[0].text.strip()})

    except YouTubeTranscriptApi.CouldNotRetrieveTranscript:
        return jsonify({'error': 'Could not retrieve the transcript for the provided YouTube video.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def fetch_transcript(youtube_url):
    video_id = youtube_url.split('v=')[-1].split('&')[0]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = ' '.join([entry['text'] for entry in transcript])
    
    # Limiting the transcript to 10240 characters
    if len(transcript_text) > 10240:
        transcript_text = transcript_text[:10240]

    # Check if the combined prompt exceeds ChatGPT's input limit
    if len(transcript_text) > 2048:
        raise ValueError('The transcript is too long for ChatGPT to handle.')
    return transcript_text

if __name__ == '__main__':
    app.run(debug=False)
