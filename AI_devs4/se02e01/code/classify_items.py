import csv
import requests
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://hub.ag3nts.org/verify"
API_KEY = os.getenv("INTERNAL_API_KEY")

BASE_PROMPT = "Classify the item as NEU or DNG.\nDNG = weapons, explosives, mines, combat devices, WMD materials.\nNEU = everything else, including reactor fuel cassettes.\nReply with exactly one word: NEU or DNG."

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_csv_and_send_requests(csv_file_path):
    """
    Process CSV file and send classification requests for each item
    """
    results = []
    logger.info(f"Starting classification process for file: {csv_file_path}")
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            code = row['code']
            description = row['description']
            
            logger.info(f"Processing item {code}: {description[:50]}...")
            full_prompt = f"{BASE_PROMPT}\n\nItem: {code}:{description}"
            payload = {
                "apikey": API_KEY,
                "task": "categorize",
                "answer": {
                    "prompt": full_prompt
                }
            }
            
            try:
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()
                response_data = response.json()
                
                logger.info(f"✓ {code} - Response: {response_data}")
                
                result = {
                    "code": code,
                    "description": description,
                    "response": response_data,
                    "status_code": response.status_code
                }
                results.append(result)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ Error processing {code}: {e}")
                error_result = {
                    "code": code,
                    "description": description,
                    "error": str(e),
                    "status_code": None
                }
                results.append(error_result)
    
    logger.info(f"Completed processing. Total items: {len(results)}")
    return results

def save_results(results, output_file="classification_results.json"):
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    csv_file_path = "categorize.csv"
    
    logger.info("Starting classification process...")
    results = process_csv_and_send_requests(csv_file_path)
    successful = len([r for r in results if 'error' not in r])
    failed = len([r for r in results if 'error' in r])

    logger.info(f"Summary - Successful: {successful}, Failed: {failed}")
    save_results(results)
    logger.info("First few results:")
    for i, result in enumerate(results[:3]):
        if 'error' not in result:
            logger.info(f"{i+1}. {result['code']}: {result['response']}")
        else:
            logger.error(f"{i+1}. {result['code']}: ERROR - {result['error']}")
