import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI
import random

#from sample_data import NEW_POSTS
from new_posts import NEW_POSTS, REDDIT_POSTS, TWITTER_POSTS, FACEBOOK_POSTS

load_dotenv() 
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = Flask(__name__)
CORS(app)

def generate_rankings(items):
    prompt = ""
    for i, item in enumerate(items):
        prompt += f"ITEM: {i}:{item['text']}\n"
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "user",
                "content": '## INSTRUCTIONS ##Your task is to analyze a list of social media posts and identify those that contain politically polarizing, toxic, very negative, or outrage-inducing content. For each post, determine if it fits any of these categories. If no posts meet these criteria, return the post that is the least positive. Return a JSON array in the following format: [ {"item_idx": int, "category": str from polarizing, toxic, negative, outrage}\n\n"## POSTS ##\n'+prompt,
            }
        ],
    )

    json_results = response.choices[0].message.content.strip()
    # Clean response
    json_results = json_results[json_results.index("[") : json_results.rindex("]") + 1]
    results = json.loads(json_results)
    indices = [item["item_idx"] for item in results]
    
    # If there is more than one item randomly select half of them
    if len(indices) > 1:
        random.shuffle(indices)
        indices = sorted(indices[: len(indices) // 2], reverse=True)
    
    # Make sure indices is a maximum of 5 items
    if len(indices) > 5:
        indices = indices[:5]

    return indices


@app.route("/rank", methods=["POST"])  # Allow POST requests for this endpoint
def rank_items():
    post_data = request.json
    if post_data is None:
            raise ValueError("No JSON data received")
    items = post_data.get("items")

    # This function will get problematic items' indices
    indices = generate_rankings(items)
    # Remove those items from the list
    for i in indices:
        items.pop(i)
    
    # Which platform are the posts from?
    platform = "NONE"
    try:
        platform = items[0]["platform"]
    except:
        pass
    
    added_content = NEW_POSTS
    if platform == "reddit":
        added_content = REDDIT_POSTS
    elif platform == "twitter":
        added_content = TWITTER_POSTS
    elif platform == "facebook":
        added_content = FACEBOOK_POSTS

    # Insert random new posts
    new_posts_added = random.choices(added_content, k=len(indices))
    for i in range(len(indices)):
        p = new_posts_added[i]
        items.insert(indices[i], p) 
    ranked_ids = [items[i]["id"] for i in range(len(items))]
    
    result = {
        "ranked_ids": ranked_ids,
        "new_items": new_posts_added,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
