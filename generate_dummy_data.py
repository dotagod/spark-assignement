#!/usr/bin/env python3
import json
import time
import requests
from faker import Faker
import random

# Initialize Faker with separate instances for different locales
fake_th = Faker('th_TH')  # Thai locale for Thailand-specific data
fake_en = Faker('en_US')  # English locale for readable text

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
    
    # Use English Faker to generate a list of realistic interests
    interests_pool = [
        fake_en.word() for _ in range(10)  # Generate some random words
    ] + [
        "gaming", "movies", "music", "fashion","dance", "cooking", 
        "travel", "reading", "hiking", "yoga", "sports", "swimming", 
        "meditation", "muay thai", "street food"
    ]
    
    genders = ["male", "female", "non-binary"]
    
    for i in range(num_users):
        # Generate a unique username with English Faker
        username = fake_en.user_name()
        user_id = f"user_{username}_{str(i+1).zfill(2)}"
        
        # Generate profile with English Faker
        profile = fake_en.profile()
        
        # Use profile age or generate random age between 18 and 40
        age = random.randint(18, 40)
        
        # Use Faker for gender or select from our list
        gender = random.choice(genders)
        
        # Generate location in a neighboring quadrant using Faker's geo capabilities
        # This creates slight variations in lat/lon to simulate nearby locations
        quadrant = i % 4  # 0: NE, 1: SE, 2: SW, 3: NW
        
        # Use Thai Faker's geo_coordinate method to generate coordinates near our base
        lat_direction = 1 if quadrant in [0, 3] else -1
        lon_direction = 1 if quadrant in [0, 1] else -1
        
        lat = fake_th.coordinate(center=base_lat, radius=radius*lat_direction)
        lon = fake_th.coordinate(center=base_lon, radius=radius*lon_direction)
        
        # Convert to float and round to 4 decimal places for realistic GPS coordinates
        lat = round(float(lat), 4)
        lon = round(float(lon), 4)
        
        # Generate 2-4 random interests using English Faker's random elements
        interests = fake_en.random_elements(
            elements=interests_pool,
            length=random.randint(2, 4),
            unique=True
        )
        
        # Create user dictionary matching the Profile model structure
        # Only include fields that match the Profile model
        user = {
            "id": user_id,
            "age": age,
            "gender": gender,
            "location": {"lat": lat, "lon": lon},
            "interests": interests
        }
        
        # Store additional metadata for the JSON file but not for API
        user_with_metadata = user.copy()
        user_with_metadata.update({
            "name": fake_en.name(),
            "email": profile['mail'],
            "job": profile['job'],
            "address": fake_en.address().replace('\n', ', '),
            "joined_date": fake_en.date_this_year().isoformat()
        })
        
        # Append the user with metadata to the list
        users.append(user_with_metadata)
    
    return users

def save_to_file(users, filename="dummy_users.json"):
    """Save generated users to a JSON file"""
    with open(filename, 'w') as f:
        json.dump(users, f, indent=2)
    print(f"Saved {len(users)} users to {filename}")

def upload_to_api(users, api_url="http://localhost:8000/profiles/bulk", max_retries=5, retry_delay=2):
    """Upload users to the API endpoint"""
    # Extract only the fields needed for the API (matching Profile model)
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
    """Print users in a readable format"""
    print(json.dumps(users, indent=2))

if __name__ == "__main__":
    try:
        # Generate 20 users around Bangkok area
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
