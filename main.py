import os
from flask import Flask, request, jsonify
import logging
import requests
from dotenv import load_dotenv
# Initialize the Aggrag object with the configuration from cforge
import asyncio

# Get the current working directory
current_dir = os.getcwd()
load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
# Replace these with your Instagram app credentials
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
INSTAGRAM_USER_NAME = os.getenv('INSTAGRAM_USER_NAME')
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
VERIFICATION_TOKEN = os.getenv(
    'VERIFICATION_TOKEN')  # This token is used to verify the webhook


@app.route('/')
def home():
  return "Hello, World! The Flask app is running."


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  if request.method == 'GET':
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    app.logger.info(
        f"Received GET request: mode={mode}, token={token}, challenge={challenge}"
    )

    if mode and token:
      return challenge, 200
    else:
      return "Invalid verification token", 403

  elif request.method == 'POST':

    app.logger.info("Received POST request")
    data = request.get_json()
    app.logger.info(f"Webhook data: {data}")
    # app.logger.info(f"Webhook data type: {type(data)}")

    # Get the comment ID
    comment_id = data.get('entry')[0].get('changes')[0].get('value').get('id')

    entry = data.get('entry')
    if entry:
      changes = entry[0].get('changes')
      if changes:
        value = changes[0].get('value')
        comment_id = value.get('id')
        comment_text = value.get('text')
        sender_id = value.get('from').get('id')
        sender_username = value.get('from').get('username')
        # Avoid replying to own bot's comments to prevent infinite loop
        if sender_id != INSTAGRAM_USER_ID and sender_username != INSTAGRAM_USER_NAME:
          # Generate a response using the Aggrag object
          loop = asyncio.new_event_loop()
          asyncio.set_event_loop(loop)
          generated_response = loop.run_until_complete(
              generate_response(comment_text))

          response = send_comment_response(comment_id, generated_response)
        else:
          app.logger.info(
              "Avoiding reply to own comment to prevent infinite loop")

    # Process the webhook data here
    return 'OK', 200


async def generate_response(comment: str):

  from library.aggrag.aggrag import AggRAG
  print(f"current working dir: {current_dir}")
  cforge_file_path = os.path.join(
      current_dir,
      "configurations/Bhai Conversation__1725816673772/iteration 1/flow-1726220592988.cforge"
  )
  rag_object = AggRAG(cforge_file_path=cforge_file_path)

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
  app.logger.info(f"User comment: {comment}")
  response = await rag_object.ragstore_chat(query=comment)
  app.logger.info(f"AI generated response: {response}")
  extracted_response = response[0].get('response', None)
  return extracted_response


def send_comment_response(comment_id, message):
  if comment_id is None:
    app.logger.error("Comment ID is missing in the webhook data.")
    return
  print("sending response")
  url = f"https://graph.instagram.com/v20.0/{comment_id}/replies"
  headers = {
      "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}",
      "Content-Type": "application/json"
  }
  data = {"message": message}
  app.logger.info(f"url: {url}, headers: {headers}, data: {data}")
  response = requests.post(url, headers=headers, json=data)
  # print(f"response recvd: {response.json()}")
  if response.status_code == 200:
    app.logger.debug(f"Comment response sent successfully: {message}")
  else:
    app.logger.error(f"Error sending comment response: {response.status_code}")

  return response


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 8000))
  app.logger.info(f"Starting application on port {port}")
  app.run(host='0.0.0.0', port=port)
