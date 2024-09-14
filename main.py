from flask import Flask, request, jsonify
import requests
import json
import os, sys
import logging
from dotenv import load_dotenv
from library.aggrag.aggrag import AggRAG
# Initialize the Aggrag object with the configuration from cforge
import asyncio

# Get the current working directory
current_dir = os.getcwd()

load_dotenv()
app = Flask(__name__)
# logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
# logging.basicConfig(filename='app.log',
#                     level=logging.DEBUG,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# Replace these with your Instagram app credentials
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
VERIFICATION_TOKEN = os.getenv(
    'VERIFICATION_TOKEN')  # This token is used to verify the webhook


# Your webhook endpoint
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  if request.method == 'GET':
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    print(f"mode: {mode}, {token}, {challenge}")
    logging.debug(f"mode: {mode}, {token}, {challenge}")

    if mode == 'subscribe' and token == VERIFICATION_TOKEN:
      return challenge, 200
    else:
      logging.error("Invalid verification token")
      return 'Invalid verification token', 403

  elif request.method == 'POST':
    logging.debug(f"Received webhook response")
    data = request.get_json()
    logging.debug(f"Received webhook data: {data}")
    print(f"Received webhook data: {data}")  # Display in Replit console
    # Log the received webhook data
    # Process the webhook data here.
    # For example:
    for entry in data['entry']:
      for change in entry['changes']:
        if change['field'] == 'comments':
          comment_data = change['value']
          logging.debug(f"Received webhook data: {data}")
          print(f"New comment: {comment_data}")
          # Get the comment ID
          comment_id = comment_data['id']
          # TODO: Generate a response using the Aggrag object
          loop = asyncio.new_event_loop()
          asyncio.set_event_loop(loop)
          response = loop.run_until_complete(
              generate_response(comment_data['text']))

          send_comment_response(comment_id,
                                "Thank you for your response, bhai.")

    return 'OK', 200

  else:
    return 'Invalid request', 400


def send_comment_response(comment_id, message):
  print("sending response")
  url = f"https://graph.instagram.com/v20.0/{comment_id}/replies"
  headers = {
      "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}",
      "Content-Type": "application/json"
  }
  data = {"message": message}
  print(f"url: {url}, headers: {headers}, data: {data}")
  response = requests.post(url, headers=headers, json=data)
  print(f"response recvd: {response.json()}")
  if response.status_code == 200:
    logging.debug(f"Comment response sent successfully: {message}")
  else:
    logging.error(f"Error sending comment response: {response.status_code}")


# Helper function to generate a user access token
def get_user_access_token(code):
  url = "https://graph.instagram.com/v20.0/oauth/access_token"
  params = {
      "client_id": INSTAGRAM_APP_ID,
      "client_secret": INSTAGRAM_APP_SECRET,
      "code": code,
      "grant_type": "authorization_code",
      "redirect_uri":
      "YOUR_REDIRECT_URI"  # Your redirect URI from the Instagram app setup
  }
  response = requests.post(url, params=params)
  if response.status_code == 200:
    return response.json()['access_token']
  else:
    return None


async def generate_response(comment: str):
  print(f"current working dir: {current_dir}")
  cforge_file_path = os.path.join(
      current_dir,
      "configurations/Bhai Conversation__1725816673772/iteration 1/flow-1726220592988.cforge"
  )
  rag_object = AggRAG(cforge_file_path=cforge_file_path)
  print(f"rag object created")
  print(f"Use case: {rag_object.usecase_name}, {rag_object.iteration}")
  # Construct the path to the 'index' directory
  index_dir = os.path.join(current_dir, 'configurations',
                           rag_object.usecase_name, rag_object.iteration,
                           'index')
  rag_object.ragstore.base.index_name = "base_index_1__1726221463705_1726222962860"
  rag_object.ragstore.base.PERSIST_DIR = index_dir
  # Update the PERSIST_DIR
  rag_object.PERSIST_DIR = index_dir

  await rag_object.retrieve_all_index_async()
  response = await rag_object.ragstore_chat(query=comment)
  print(response)
  return response


if __name__ == '__main__':
  # asyncio.run(main())
  app.run(debug=True)
