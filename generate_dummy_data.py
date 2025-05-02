#!/usr/bin/env python3
import json
import time
import requests
from faker import Faker
import random

fake_th = Faker('th_TH')
fake_en = Faker('en_US')

def generate_user_data(num_users=10, base_lat=13.7563, base_lon=100.5018, radius=0.01):
    """
    Generate realistic dummy user data with neighboring quadrant location variations.
    
    Args:
        num_users: Number of users to generate
        base_lat: Base latitude to generate locations around (Bangkok default)
        base_lon: Base longitude to generate locations around (Bangkok default)
        radius: Maximum distance from base coordinates (in degrees)
        
    Returns:
        List of user dictionaries
    """
    users = []
    
    interests_pool = [
        fake_en.word() for _ in range(10)
    ] + [
        "gaming", "movies", "music", "fashion","dance", "cooking", 
        "travel", "reading", "hiking", "yoga", "sports", "swimming", 
        "meditation", "muay thai", "street food"
    ]
    
    genders = ["male", "female", "non-binary"]
    
    for i in range(num_users):
        username = fake_en.user_name()
        user_id = f"user_{username}_{str(i+1).zfill(2)}"
        
        profile = fake_en.profile()
        
        age = random.randint(18, 40)
        
        gender = random.choice(genders)
        
        quadrant = i % 4
        
        lat_direction = 1 if quadrant in [0, 3] else -1
        lon_direction = 1 if quadrant in [0, 1] else -1
        
        lat = fake_th.coordinate(center=base_lat, radius=radius*lat_direction)
        lon = fake_th.coordinate(center=base_lon, radius=radius*lon_direction)
        
        lat = round(float(lat), 4)
        lon = round(float(lon), 4)
        
        interests = fake_en.random_elements(
            elements=interests_pool,
            length=random.randint(2, 4),
            unique=True
        )
        
        user = {
            "id": user_id,
            "age": age,
            "gender": gender,
            "location": {"lat": lat, "lon": lon},
            "interests": interests
        }
        
        user_with_metadata = user.copy()
        user_with_metadata.update({
            "name": fake_en.name(),
            "email": profile['mail'],
            "job": profile['job'],
            "address": fake_en.address().replace('\n', ', '),
            "joined_date": fake_en.date_this_year().isoformat()
        })
        
        users.append(user_with_metadata)
    
    return users

def save_to_file(users, filename="dummy_users.json"):
    """Save generated users to a JSON file"""
    with open(filename, 'w') as f:
        json.dump(users, f, indent=2)
    print(f"Saved {len(users)} users to {filename}")

def upload_to_api(users, api_url="http://localhost:8000/profiles/bulk", max_retries=5, retry_delay=2):
    api_users = []
    for user in users:
        api_user = {
            "id": user["id"],
            "age": user["age"],
            "gender": user["gender"],
            "location": user["location"],
            "interests": user["interests"]
        }
        api_users.append(api_user)
    
    # Try to upload to API with retries
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=api_users)
            if response.status_code == 200:
                print(f"Successfully uploaded {len(api_users)} users to API")
                return True
            else:
                print(f"API upload failed with status code {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            print(f"API upload attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print("Failed to upload users to API after multiple attempts")
    return False

def print_users(users):
    print(json.dumps(users, indent=2))

if __name__ == "__main__":
    try:
        users = generate_user_data(
            num_users=100, 
            base_lat=13.7563, 
            base_lon=100.5018,
            radius=0.01
        )
    
        # Save to file
        save_to_file(users)
        
        # Try to upload to API (will retry a few times if server isn't ready yet)
        upload_to_api(users)
        
    except Exception as e:
        print(f"Error generating dummy data: {e}")
