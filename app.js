'use strict';

require('dotenv').config()

const {Client, middleware} = require('@line/bot-sdk');
const express = require('express');

const { Configuration, OpenAIApi } = require("openai");

// create LINE SDK config from env variables
const config = {
    channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
    channelSecret: process.env.CHANNEL_SECRET,
};

// create LINE SDK client
const lineClient = new Client(config);

// create Express app
// about Express itself: https://expressjs.com/
const app = express();

const configuration = new Configuration({
    apiKey: process.env.OPENAI_API_KEY,
});

const openaiClient = new OpenAIApi(configuration);

// event handler
async function handleEvent(event) {
    if (event.type !== 'message' || event.message.type !== 'text') {
        // ignore non-text-message event
        return Promise.resolve(null);
    }

    const response = await openaiClient.createCompletion({
        model: "text-davinci-003",
        prompt: event.message.text,
        temperature: 0.7,
        max_tokens: 256,
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0,
    });

    if (!response.data.choices.length) {
        return Promise.resolve(null);
    }

    const choice = response.data.choices[0];

    // create an echoing text message
    const echo = { type: 'text', text: choice.text.trim() };

    // use reply API
    return lineClient.replyMessage(event.replyToken, echo);
}

// register a webhook handler with middleware
// about the middleware, please refer to doc
app.post('/webhook', middleware(config), (req, res) => {
    Promise
        .all(req.body.events.map(handleEvent))
        .then((result) => res.json(result))
        .catch((err) => {
            console.error(err);
            res.status(500).end();
        });
});

// listen on port
const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`listening on ${port}`);
});
