import argparse
import bibtexparser
from openai import OpenAI
import os
import re
import csv
from dotenv import load_dotenv
import logging
from time import perf_counter
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Get model from .env

def parse_response(response_text: str) -> Dict[str, str]:
    """Parse the LLM response to extract status, criteria, and reasoning"""
    try:
        status_match = re.search(r'Status:\s*(accepted|rejected|not-sure)', response_text, re.IGNORECASE)
        criteria_match = re.search(r'Criteria:\s*((CI|CX)\d+)', response_text)
        reasoning_match = re.search(r'Reasoning:\s*(.*)', response_text, re.DOTALL)

        return {
            'status': (status_match.group(1).lower() if status_match else 'not-sure'),
            'criteria': (criteria_match.group(1) if criteria_match else 'not-specified'),
            'reasoning': (reasoning_match.group(1).strip() if reasoning_match else '')
        }
    except Exception as e:
        logging.error(f"Failed to parse response: {e}")
        return {'status': 'not-sure', 'criteria': 'parse-error', 'reasoning': 'Response parsing failed'}

def evaluate_entry(title: str, abstract: str, criteria_content: str, model_name: str) -> Dict[str, str]:
    """Query OpenAI API to evaluate a paper entry"""
    prompt = f"""Evaluate the paper based on these criteria:

{criteria_content}

Title: {title}
Abstract: {abstract}

Respond STRICTLY in this format:
Status: [accepted/rejected/not-sure]
Criteria: [CIn/CXn/not-applicable]
Reasoning: [Brief explanation linking to specific criteria]"""

    try:
        start_time = perf_counter()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a systematic review assistant. Use the exact response format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        elapsed = perf_counter() - start_time
        logging.debug(f"API call completed in {elapsed:.2f}s")
        return parse_response(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"API Error: {e}")
        return {'status': 'not-sure', 'criteria': 'api-error', 'reasoning': 'Evaluation failed'}

def load_criteria(criteria_path: str) -> str:
    """Load evaluation criteria from markdown file"""
    try:
        with open(criteria_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Criteria file not found: {criteria_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading criteria file: {e}")
        raise

def load_bib_entries(input_path: str) -> List[Dict]:
    """Load and parse BibTeX entries from file"""
    try:
        with open(input_path, encoding="utf-8") as f:
            return bibtexparser.load(f).entries
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logging.error(f"Error parsing BibTeX file: {e}")
        raise

def process_entries(entries: List[Dict], criteria_content: str, model_name: str) -> List[Dict]:
    """Process all bibliography entries through evaluation"""
    results = []
    total_entries = len(entries)
    
    for idx, entry in enumerate(entries, 1):
        progress = (idx / total_entries) * 100
        logging.info(f"Processing entry {idx}/{total_entries} ({progress:.2f}%) - {entry.get('ID', 'N/A')}")
        
        evaluation = evaluate_entry(
            entry.get('title', ''),
            entry.get('abstract', ''),
            criteria_content,
            model_name
        )
        
        results.append({
            'citekey': entry.get('ID', 'N/A'),
            'title': entry.get('title', ''),
            'status': evaluation['status'],
            'criteria': evaluation['criteria'],
            'reasoning': evaluation['reasoning']
        })
        
        logging.info(f"Result: {evaluation['status']} ({evaluation['criteria']}) - {evaluation['reasoning'][:50]}...")
    
    return results

def write_results_to_csv(results: List[Dict], output_path: str) -> None:
    """Write evaluation results to CSV file"""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['citekey', 'title', 'status', 'criteria', 'reasoning'])
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Results successfully written to {output_path}")
    except Exception as e:
        logging.error(f"Error writing CSV file: {e}")
        raise

def calculate_statistics(results: List[Dict]) -> None:
    """Calculate and log evaluation statistics"""
    counts = {'accepted': 0, 'rejected': 0, 'not-sure': 0}
    criteria_counts = {}
    
    for item in results:
        counts[item['status']] += 1
        criteria = item['criteria']
        criteria_counts[criteria] = criteria_counts.get(criteria, 0) + 1
    
    total = len(results)
    logging.info("\nFinal Results:")
    for status in ['accepted', 'rejected', 'not-sure']:
        logging.info(f"{status.capitalize()}: {counts[status]} ({counts[status]/total:.1%})")
    
    logging.info("\nCriteria Breakdown:")
    for criteria, count in sorted(criteria_counts.items()):
        logging.info(f"{criteria}: {count} ({count/total:.1%})")

def process_bib(input_path: str, output_path: str, criteria_path: str = 'criteria.md') -> None:
    """Main processing pipeline"""
    try:
        criteria_content = load_criteria(criteria_path)
        entries = load_bib_entries(input_path)
        results = process_entries(entries, criteria_content, MODEL_NAME)
        write_results_to_csv(results, output_path)
        calculate_statistics(results)
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Survey Classifier')
    parser.add_argument('-i', '--input', default='input.bib', help='Input BibTeX file path (default: input.bib)')
    parser.add_argument('-o', '--output', default='results.csv', help='Output CSV file path (default: results.csv)')
    parser.add_argument('-c', '--criteria', default='criteria.md', 
                      help='Path to criteria file (default: criteria.md)')
    return parser.parse_args()

if __name__ == "__main__":
    start_time = perf_counter()
    args = parse_arguments()
    
    try:
        process_bib(
            input_path=args.input,
            output_path=args.output,
            criteria_path=args.criteria
        )
    except Exception as e:
        logging.error(f"Fatal error occurred: {e}")
    finally:
        elapsed = perf_counter() - start_time
        logging.info(f"Total processing time: {elapsed:.2f} seconds")