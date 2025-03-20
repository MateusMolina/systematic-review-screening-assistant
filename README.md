# Systematic Review Screening Assistant

AI-powered tool for screening academic papers during systematic reviews. Evaluates bibliography entries against custom criteria using LLM models.

## Features

- Processes BibTeX files with paper metadata
- Uses AI to evaluate inclusion/exclusion criteria
- Generates CSV report with decisions
- Creates filtered bibliography of accepted papers

## Quick Start


0. **(optional) Fix inconsistencies in your bib file**

Using [bibtex-tidy](https://github.com/FlamingTempura/bibtex-tidy) cli: 

```bash
bibtex-tidy --curly --numeric --tab --align=13 --duplicates=key --no-escape --sort-fields --no-remove-dupe-fields --generate-keys YOUR_FILE.bib
```

Also available as a [free web app](https://flamingtempura.github.io/bibtex-tidy/index.html).

1. **Install requirements**
```bash
pip install -r requirements.txt
```

2. **Configure environment**
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

3. **Run screening**
```bash
python survey_classifier.py -i input.bib -o results.csv
```

4. **Generate accepted papers from results.csv**
```bash
python generate_accepted_bib.py -i input.bib -r results.csv -o accepted.bib
```

## Configuration

### Criteria File (`criteria.md`)

Define your inclusion and exclusion criterias. For an example, see the included `criteria.md`.

### Environment Variables (`.env`)

```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo  # Optional model override
```

### Default File Structure

```
input.bib       # Source bibliography
criteria.md     # Evaluation criteria
results.csv     # Output decisions
accepted.bib    # Filtered bibliography
```

## Usage Options

**Custom file paths:**
```bash
python survey_classifier.py \
  -i custom_input.bib \
  -o custom_results.csv \
  -c custom_criteria.md
```

## Output Example

`results.csv` columns:

```csv
citekey,title,status,criteria,reasoning
smith2023,ML Study,accepted,CI1,"Matches machine learning focus"
```

⚠️ **Note:** API usage costs may apply. Review OpenAI pricing before large-scale use.
