import requests
import logging
from app.models import Herb, db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Plant.id API configuration
PLANT_ID_API_KEY = "3xGm829HGqEJvwXbCFqEu3O4UCIDm1eCrQSzMsDPEpb4jbZR1C"  # Replace with your actual API key
PLANT_ID_API_URL = "https://api.plant.id/v2/identify"

def identify_plant(image_url):
    """
    Identify a plant using the Plant.id API.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Api-Key": "3xGm829HGqEJvwXbCFqEu3O4UCIDm1eCrQSzMsDPEpb4jbZR1C"  # Replace with your actual API key
        }
        payload = {
            "images": [image_url],
            "modifiers": ["common_names", "scientific_names"],
            "plant_details": ["common_names", "scientific_name", "part_used", "toxicity", "description"]
        }

        logger.info(f"Identifying plant from image URL: {image_url}")
        response = requests.post("https://api.plant.id/v2/identify", json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()

        logger.info("Plant identification successful")
        return result

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return None

def fetch_and_save_plant_details(herb_name):
    """
    Fetch plant details from the Plant.id API and save them to the database.

    Args:
        herb_name (str): The name of the herb to search for.

    Returns:
        list: A list of saved Herb objects if successful, otherwise None.
    """
    try:
        # Step 1: Search for plants using Plant.id API
        search_url = "https://plant.id/api/v3/kb/plants/name_search"
        search_params = {
            "q": herb_name,  # Plant name to search for
            "limit": 10      # Limit the number of results
        }
        search_headers = {
            "Api-Key": PLANT_ID_API_KEY,  # Use the same API key
            "Content-Type": "application/json"
        }

        logger.info(f"Searching for plant: {herb_name}")
        search_response = requests.get(search_url, headers=search_headers, params=search_params)
        search_response.raise_for_status()  # Raise an exception for HTTP errors
        search_data = search_response.json()

        # Check if any results were found
        if not search_data.get("entities"):
            logger.warning(f"No results found for plant: {herb_name}")
            return None

        # Step 2: Fetch detailed information for each plant
        saved_herbs = []
        for entity in search_data["entities"]:
            access_token = entity.get("access_token")
            if not access_token:
                logger.warning("No access token found for plant entity")
                continue

            # Fetch detailed information for the plant
            details_url = f"https://plant.id/api/v3/kb/plants/{access_token}"
            details_params = {
                "details": "common_names,url,description,taxonomy,rank,gbif_id,inaturalist_id,image,synonyms,edible_parts,watering,propagation_methods"
            }
            logger.info(f"Fetching details for plant with access token: {access_token}")
            details_response = requests.get(details_url, headers=search_headers, params=details_params)
            details_response.raise_for_status()
            details_data = details_response.json()

            # Extract relevant fields from the detailed response
            common_name = details_data.get("common_names", ["Unknown"])[0]  # Use the first common name
            scientific_name = details_data.get("name", "Unknown")
            family = details_data.get("taxonomy", {}).get("family", "Unknown")
            image_url = details_data.get("image", {}).get("value", "No image available")
            part_used = ", ".join(details_data.get("edible_parts", ["Unknown"]))
            toxicity = "Non-toxic" if details_data.get("edible_parts") else "Unknown"
            description = details_data.get("description", {}).get("value", "No description available")
            watering = f"Min: {details_data.get('watering', {}).get('min', 'Unknown')}, Max: {details_data.get('watering', {}).get('max', 'Unknown')}"
            propagation_methods = ", ".join(details_data.get("propagation_methods", ["Unknown"]))

            # Check if the herb already exists in the database
            existing_herb = Herb.query.filter_by(scientific_name=scientific_name).first()
            if existing_herb:
                logger.info(f"Herb already exists in the database: {scientific_name}")
                continue

            # Create a new Herb entry
            new_herb = Herb(
                common_name=common_name,
                scientific_name=scientific_name,
                family=family,
                image_url=image_url,
                part_used=part_used,
                toxicity=toxicity,
                description=description,
                watering=watering,
                propagation_methods=propagation_methods
            )
            db.session.add(new_herb)
            saved_herbs.append(new_herb)
            logger.info(f"Saved new herb: {scientific_name}")

        # Commit the changes to the database
        db.session.commit()
        logger.info(f"Successfully saved {len(saved_herbs)} herbs to the database")

        return saved_herbs

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        return None