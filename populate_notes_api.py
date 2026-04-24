import urllib.request
import urllib.error
import urllib.parse
import json
import random
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxOCwidG9rZW5fdHlwZSI6ImFjY2VzcyIsImV4cCI6MTc3NzAxNTY4NiwiaWF0IjoxNzc3MDEyMDg2fQ.KQnthmKUXnz9SoX0VUJ3l0PxUUMBz4Be56J8IMCY1zI"
BASE_URL = "http://127.0.0.1:8000/api/notes/"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Pre-defined list of titles and contents to make it realistic
titles = ["Meeting Notes", "Grocery List", "Project Ideas", "Daily Journal", "To-Do List", "Books to Read", "Movie Recommendations", "Workout Plan", "Travel Itinerary", "Recipe Idea", "Gift Ideas", "Expense Tracker", "Tech Stack Ideas", "Weekend Plans", "Dream Log"]
contents = ["Need to discuss the new feature.", "Eggs, Milk, Bread, Apples.", "Build a new app using Django and React.", "Today was a good day. I worked on my project.", "1. Finish coding, 2. Walk the dog, 3. Read a book.", "The Great Gatsby, 1984, To Kill a Mockingbird.", "Inception, The Matrix, Interstellar.", "Pushups, Pullups, Squats.", "Paris, Rome, London.", "Pasta with tomato sauce and cheese.", "Watch for mom, shoes for dad.", "Spent $50 on groceries.", "React, Node, Express, MongoDB.", "Go for a hike and then watch a movie.", "I dreamt about flying cars."]
colors = ["#ffffff", "#f28b82", "#fbbc04", "#fff475", "#ccff90", "#a7ffeb", "#cbf0f8", "#aecbfa", "#d7aefb", "#fdcfe8", "#e6c9a8", "#e8eaed"]

print("Starting to populate notes...")
for i in range(1, 51):
    data = {
        "title": f"{random.choice(titles)} {i}",
        "content": f"{random.choice(contents)} - generated text {i}",
        "color": random.choice(colors),
        "is_pinned": random.choice([True, False, False, False]),
        "is_archived": random.choice([True, False, False, False, False])
    }
    
    req = urllib.request.Request(BASE_URL, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                print(f"Created note {i}/50: {data['title']}")
            else:
                print(f"Failed to create note {i}. Status: {response.status}")
    except urllib.error.URLError as e:
        print(f"Failed to create note {i}. Error: {e}")
    
    # Tiny delay
    time.sleep(0.05)

print("Done populating notes via API.")
