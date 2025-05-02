# In-Memory Matchmaking Engine

A high-performance in-memory matchmaking engine built with FastAPI.

## Architecture

### Data Structures
- **Profile Store**: Dictionary mapping user IDs to Profile objects
- **Geohash Index**: Dictionary mapping geohash quadrants to sets of user IDs
- **Match Score Cache**: Dictionary mapping user IDs to their precomputed match scores
- **Exclusion Lists**: Sets for tracking blocked/disliked/matched users per user

### Matching Algorithm
1. **Geohash Filtering**: First-pass filtering using geohash quadrants (precision 5)
2. **Score Computation**:
   - Age similarity (weighted 30%)
   - Shared interests (weighted 40%)
   - Location proximity (weighted 30%)
3. **Exclusion Processing**: Filter out blocked/matched/disliked users
4. **Caching Strategy**: Precompute scores on profile creation

## Setup and Running

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --reload
```

## API Endpoints

- POST /profiles - Register new user profile
- GET /match/{id} - Get top 5 matches for a user
