import bibtexparser
import csv
import logging
from time import perf_counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

def create_accepted_bib(original_bib, results_csv, output_file='accepted.bib'):
    """
    Create a new bib file containing only accepted entries
    Args:
        original_bib: Path to original bibliography file
        results_csv: Path to evaluation results CSV
        output_file: Output path for accepted entries
    """
    try:
        start_time = perf_counter()
        
        # Load evaluation results
        accepted_keys = set()
        with open(results_csv, encoding="utf8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'].lower() == 'accepted':
                    accepted_keys.add(row['citekey'])
        
        logging.info(f"Found {len(accepted_keys)} accepted entries in results")
        
        # Load original bibliography
        with open(original_bib, encoding="utf8") as f:
            bib_db = bibtexparser.load(f)
        
        # Filter accepted entries
        accepted_entries = [
            entry for entry in bib_db.entries
            if entry.get('ID', '') in accepted_keys
        ]
        
        # Create new database
        new_db = bibtexparser.bibdatabase.BibDatabase()
        new_db.entries = accepted_entries
        
        # Write output
        with open(output_file, 'w', encoding="utf8") as f:
            bibtexparser.dump(new_db, f)
            
        elapsed = perf_counter() - start_time
        logging.info(f"Created {output_file} with {len(accepted_entries)} entries in {elapsed:.2f}s")
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create accepted papers bibliography from evaluation results'
    )
    parser.add_argument('--input', '-i', default='input.bib',
                      help='Original bibliography file')
    parser.add_argument('--results', '-r', default='results.csv',
                      help='Evaluation results CSV file')
    parser.add_argument('--output', '-o', default='accepted.bib',
                      help='Output file for accepted entries')
    
    args = parser.parse_args()
    
    create_accepted_bib(
        original_bib=args.input,
        results_csv=args.results,
        output_file=args.output
    )