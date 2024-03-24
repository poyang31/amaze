from os import getenv
from random import choice

from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# LINE Messaging API config
line_channel_access_token = getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_channel_secret = getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# OpenAI config
openai_base_url = getenv("OPENAI_BASE_URL")
openai_api_key = getenv("OPENAI_API_KEY")
openai_model = getenv("OPENAI_MODEL")
openai_client = OpenAI(
    base_url=openai_base_url,
    api_key=openai_api_key,
)

# Flask config
app = Flask(__name__)


# Webhook endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# Message event handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Ignore non-text-message event
    if not isinstance(event.message, TextMessage):
        return

    # Get text from the message
    user_text = event.message.text

    # Generate completion using OpenAI
    completion = openai_client.chat.completions.create(
        model=openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a assistant.",
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
    )

    # Extract the completion from OpenAI
    completion_choice = choice(completion.choices)
    completion_content = completion_choice.message.content

    # Check completion
    if not completion_content:
        return

    # Reply to the user with the generated response
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=completion_content.strip()),
    )
