"""
API client for fetching UF values from the CMF (Comisión para el Mercado Financiero) API.
"""

import requests
from datetime import date
from typing import Optional

def fetch_uf_value_from_api(target_date: date, api_key: str) -> Optional[float]:
    """
    Fetches the UF value for a specific date from the CMF API.
    Returns the float value or None if not found or an error occurs.
    """
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("Error: API key not configured. Please set your CMF API key in cmfkey.")
        return None

    year = target_date.year
    month = target_date.month
    day = target_date.day
    
    url = f"https://api.cmfchile.cl/api-sbifv3/recursos_api/uf/{year}/{month}/dias/{day}?apikey={api_key}&formato=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # The API returns a list with a single dictionary
        if "UFs" in data and data["UFs"]:
            value_str = data["UFs"][0]["Valor"]
            # The value is a string with a comma as a decimal separator
            cleaned_value_str = value_str.replace('.', '').replace(',', '.')
            return float(cleaned_value_str)
        else:
            print(f"API response did not contain UF value for {target_date}: {data}")
            return None

    except requests.RequestException as e:
        print(f"Error fetching UF data from CMF API for {target_date}: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error parsing UF value from API response for {target_date}: {e}")
        return None
