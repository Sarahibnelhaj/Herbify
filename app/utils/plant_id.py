import os
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def fetch_plant_data(plant_name):
    """
    Fetch plant data from Plant.id API based on plant name.

    Args:
        plant_name (str): The name of the plant to search for.

    Returns:
        dict: A dictionary containing plant data from the Plant.id API.

    Raises:
        ValueError: If the Plant.id API key is missing.
        Exception: If there is an issue with the Plant.id API request or response.
    """
    # Fetch the Plant.id API key from environment variables
    PLANT_API_KEY = os.getenv("PLANT_API_KEY")
    if not PLANT_API_KEY:
        logger.error("Plant.id API key not found in environment variables.")
        raise ValueError("Plant.id API key not found in environment variables.")

    # Construct the Plant.id API URL
    url = "https://api.plant.id/v3/identification"
    headers = {
        "Api-Key": PLANT_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "query": plant_name,  # Use the plant name as the query
        "details": ["common_names", "scientific_name", "family", "image_url"],  # Requested details
        "similar_images": True  # Include similar images in the response
    }

    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Parse the JSON response
        data = response.json()
        logger.info(f"Plant.id API response: {data}")

        # Check if the response contains valid data
        if not data.get("result", {}).get("classification", {}).get("suggestions"):
            logger.warning(f"No results found for the plant: {plant_name}")
            raise Exception("No results found for the given plant name.")

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Plant.id API: {e}")
        raise Exception(f"Plant.id API is currently unavailable: {e}")

    except Exception as e:
        logger.error(f"Unexpected error while fetching data from Plant.id API: {e}")
        raise Exception(f"An unexpected error occurred: {e}")