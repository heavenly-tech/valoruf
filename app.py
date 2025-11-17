"""
Main Flask application for the Valoruf API.
Handles API requests for UF values, caching, and serving the frontend.
"""
import time
import csv
import io
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request, Response, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# Use the new API client
from uf_api import fetch_uf_value_from_api

# --- Config and Environment Loading ---
# Load environment variables (including CMF_API_KEY and FRONTEND_ORIGIN)
load_dotenv() 

CACHE_FILENAME = "uf_cache.csv"
CACHE_EXPIRATION_SECONDS = 3600  # 1 hour

# Get config variables directly from environment
api_key = os.getenv('CMF_API_KEY')
# Use the environment variable for origin, falling back to '*' for max compatibility (dev/testing)
ALLOWED_ORIGIN = os.getenv('FRONTEND_ORIGIN', '*') 


# --- Application Setup ---
app = Flask(__name__, static_folder='.', static_url_path='')

# Configure CORS explicitly for security/dynamism
CORS(app, resources={
    # Apply this specific configuration to all routes starting with /api/
    r"/api/*": {
        "origins": ALLOWED_ORIGIN,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

if not api_key or api_key == "YOUR_API_KEY_HERE":
    print("Warning: CMF_API_KEY environment variable not set or is a placeholder.")
else:
    print("API key loaded from environment.")

# --- In-memory Cache ---
data_cache = {}


# --- Cache and Key Loading ---

def load_cache_from_csv():
    """Loads the cache from the CSV file into the in-memory dictionary."""
    if not os.path.exists(CACHE_FILENAME):
        with open(CACHE_FILENAME, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "value", "timestamp"])
        return

    with open(CACHE_FILENAME, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header: return
        for row in reader:
            date_str, value_str, timestamp_str = row
            data_cache[date_str] = {
                "value": float(value_str),
                "timestamp": float(timestamp_str)
            }
    print(f"Cache loaded from {CACHE_FILENAME}: {len(data_cache)} items.")

def append_to_csv(date_str, value, timestamp):
    """Appends a new entry to the cache CSV file."""
    with open(CACHE_FILENAME, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date_str, value, timestamp])

# --- Core Logic ---

def date_from_str(date_str: str):
    """Safely converts YYYY-MM-DD string to a date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def get_uf_value_with_cache(target_date):
    """
    Fetches UF value, using cache first, then falling back to the API.
    Returns a tuple: (value, was_cached).
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    if date_str in data_cache and (time.time() - data_cache[date_str]["timestamp"] < CACHE_EXPIRATION_SECONDS):
        print(f"Cache HIT for date: {date_str}")
        return data_cache[date_str]["value"], True

    print(f"Cache MISS for date: {date_str}. Fetching from CMF API...")
    
    # Fetch from the CMF API
    value = fetch_uf_value_from_api(target_date, api_key)
    if value is None:
        print(f"Failed to fetch value for {date_str} from API.")
        return None, False

    timestamp = time.time()
    data_cache[date_str] = {"timestamp": timestamp, "value": value}
    append_to_csv(date_str, value, timestamp)
    print(f"New value for '{date_str}' ({value}) cached.")
    return value, False

# --- API Endpoints ---

@app.route("/api/uf/<date_str>", methods=["GET"])
def get_uf_for_date(date_str):
    """API endpoint for a single date."""
    target_date = date_from_str(date_str)
    if not target_date:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    value, cached = get_uf_value_with_cache(target_date)
    if value is None:
        return jsonify({"error": f"Could not retrieve UF value for {date_str}."}), 404

    output_format = request.args.get("format", "json").lower()
    if output_format == "raw":
        return Response(str(value), mimetype='text/plain')
    
    return jsonify({"date": date_str, "value": value, "cached": cached})


@app.route("/api/uf/<start_date_str>/<end_date_str>", methods=["GET"])
def get_uf_for_range(start_date_str, end_date_str):
    """API endpoint for a date range."""
    start_date = date_from_str(start_date_str)
    end_date = date_from_str(end_date_str)

    if not start_date or not end_date:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    if start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date."}), 400

    results = []
    current_date = start_date
    while current_date <= end_date:
        value, cached = get_uf_value_with_cache(current_date)
        if value is not None:
            results.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "cached": cached})
        current_date += timedelta(days=1)

    if not results:
        return jsonify({"error": "No data found for the specified range."}), 404

    output_format = request.args.get("format", "json").lower()
    if output_format == "csv":
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["date", "value", "cached"])
        cw.writerows([[row["date"], row["value"], row["cached"]] for row in results])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=uf_values.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return jsonify(results)

@app.route("/api/uf/cached", methods=["GET"])
def get_cached_uf_values():
    """API endpoint to return all cached UF values from memory."""
    results = [
        {"date": date, "value": cache_item["value"], "cached": True}
        for date, cache_item in data_cache.items()
    ]
    if not results:
        return jsonify({"message": "Cache is currently empty."}), 404
    return jsonify(results)

# --- Frontend Route ---

@app.route("/", methods=["GET"])
def serve_frontend():
    """Serves the static index.html file."""
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    load_cache_from_csv()
    app.run(debug=True, port=5000)
