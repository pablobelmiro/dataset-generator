# XML Synthetic Dataset Generator

This project provides a complete pipeline to ingest sample XML files and expand them into a large synthetic dataset using realistic Brazilian data.

## Features
- **Automatic Template Creation**: Uses `lxml` to parse existing XMLs and convert them into Jinja2 templates.
- **Realistic Data**: Uses `faker` (customized with `pt_BR` locale) to generate names, documents (CPF/CNPJ), addresses, and product info.
- **Validations**: Generates valid CPF/CNPJ checksums using Faker's built-in providers.
- **Dynamic Mapping**: Uses a heuristic regex-based engine (`src/dynamic_mapper.py`) to infer data types from XML tag names at runtime. No manual mapping file required!

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install faker lxml jinja2
   ```

## Usage

1. Place your source XML files in the `sampling_files/` directory.
2. Run the main script:
   ```bash
   # Generate 10 files (default)
   python -m src.main
   
   # Generate 100 files
   python -m src.main --count 100
   ```
3. Check the `output/` directory for results.

## Technical Explanations

### Dynamic Mapping (Heuristics)
Instead of a static configuration file, the `DynamicMapper` class scans the input XML tags and applies regex patterns to decide how to fill them.
- **Rules**: Defined in `src/dynamic_mapper.py`.
- **Example**: Any tag matching `(?i)CPF` is automatically mapped to `person.cpf`. Any tag matching `(?i)vProd` is mapped to `product.price`.

### Handling Repeating Fields and Totals
In real-world scenarios, certain fields like `vNF` (Total Value of Invoice) must be the exact sum of item values (`vProd`).

**Current Approach (MVP):**
The current implementation generates random values for each tag independently to maximize variability for NLP/RAG training. This means `vProd` and `vNF` might not mathematically match in the synthetic output.

**Recommended Strategy for Consistency:**
To enforce mathematical consistency (e.g., `Total = Sum(Items)`):
1. **Two-Pass Generation**: 
   - First, generate the line items (products, quantities, prices) and store them in a list/object.
   - Calculate the sum of these items.
   - Pass both the items list and the calculated total into the template context.
2. **Jinja2 Loops**:
   - Instead of treating every tag as a leaf node to be replaced, allow the template to contain loops (`{% for item in items %}`).
   - The `XMLProcessor` would need to identify repeating blocks (like `<det>`) and wrap them in a loop structure in the template, rather than just replacing inner text.
   - This requires a more complex "schema inference" step to detect which blocks are repeatable.

For this project, we focused on *structural* variability and realistic *individual* field data, which is often sufficient for Named Entity Recognition (NER) tasks.
