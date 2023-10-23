from flask import Flask, request, jsonify
import os
import openai  # Import the openai library
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from datetime import timedelta, datetime




app = Flask(__name__)

# Constants
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY  # Set the API key
YOUTUBE_API_KEY = 'AIzaSyBIB84RbnY_3RkmEgTlilt--dx4_MPW40A'


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

@app.route('/ask_question', methods=['POST']) #Is post request
def ask_question():
    data = request.get_json()  # New line to get data from JSON body
    youtube_url = data.get('youtube_url')  # Change from request.args.get to data.get
    question = data.get('question')  # Change from request.args.get to data.get

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
def get_top_3_videos(api_key, query, recency_year, n=3):
    youtube = build('youtube', 'v3', developerKey=api_key)

    current_year = datetime.now().year
    cutoff_year = current_year - recency_year

    search_response = youtube.search().list(
        q=query,
        type="video",
        order="viewCount",
        part="id,snippet",
        maxResults=10
    ).execute()

    video_candidates = []
    for item in search_response['items']:
        video_id = item['id']['videoId']

        video_response = youtube.videos().list(
            id=video_id,
            part="contentDetails,statistics,snippet"
        ).execute()

        video = video_response['items'][0]
        publication_year = int(video['snippet']['publishedAt'][:4])

        if publication_year >= cutoff_year:
            duration = timedelta(seconds=sum(int(x) * 60**i for i, x in enumerate(reversed(video['contentDetails']['duration'][2:-1].split('M')))))

            if timedelta(minutes=1) < duration < timedelta(hours=1):
                likes = int(video['statistics'].get('likeCount', 0))
                dislikes = int(video['statistics'].get('dislikeCount', 0))
                views = int(video['statistics']['viewCount'])
                ratio = likes / (likes + dislikes) if (likes + dislikes) > 0 else 0
                
                score = views * (ratio ** n)

                video_candidates.append({
                    'score': score,
                    'title': video['snippet']['title'],
                    'link': f"https://www.youtube.com/watch?v={video_id}",
                    'published_at': video['snippet']['publishedAt'],
                    'channel_title': video['snippet']['channelTitle'],
                    'view_count': views,
                    'like_count': likes,
                    'dislike_count': dislikes
                })

    top_videos = sorted(video_candidates, key=lambda x: x['score'], reverse=True)[:3]
    return top_videos
@app.route('/youtube_summary', methods=['POST'])
def youtube_summary():
    data = request.get_json()
    prompt = data.get('prompt')
    recency = data.get('recency', 2)

    if not prompt:
        return jsonify({'error': 'Prompt parameter is required'}), 400

    try:
        videos = get_top_3_videos(YOUTUBE_API_KEY, prompt, recency)
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500





if __name__ == '__main__':
    app.run(debug=True)
