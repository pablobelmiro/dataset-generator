import os
import random
import argparse
from pathlib import Path
from jinja2 import Template
from src.xml_processor import XMLProcessor
from src.data_generator import DataFactory
from src.dynamic_mapper import DynamicMapper

# Configuration defaults
INPUT_DIR = Path('sampling_files')
OUTPUT_DIR = Path('output')
NUM_FILES = 10  # Default number of files to generate

def main():
    parser = argparse.ArgumentParser(description="XML Dataset Generator Pipeline")
    parser.add_argument('--count', type=int, default=NUM_FILES, help='Number of files to generate')
    args = parser.parse_args()

    # 1. Setup
    print(f"Starting pipeline. Target: {args.count} files.")
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    processor = XMLProcessor()
    factory = DataFactory()
    mapper = DynamicMapper()
    
    # 2. Ingest, Map, and Create Templates
    templates = []
    input_files = list(INPUT_DIR.glob('*.xml'))
    
    if not input_files:
        print(f"No XML files found in {INPUT_DIR}. Please add some sample files.")
        return

    print(f"Found {len(input_files)} source files. Creating templates with Dynamic Mapping...")
    for xml_file in input_files:
        try:
            tree = processor.ingest_xml(str(xml_file))
            
            # Dynamic Step: Analyze file to create mapping
            file_mapping = mapper.analyze_root(tree.getroot())
            # print(f"   [Debug] Mapping for {xml_file.name}: {file_mapping}")
            
            template_str = processor.create_template(tree, file_mapping)
            templates.append(Template(template_str))
            print(f" - Processed {xml_file.name} (Mapped {len(file_mapping)} tags)")
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")

    if not templates:
        print("No templates created. Exiting.")
        return

    # 3. Generation Loop
    print("Generating files...")
    
    # Wrapper function to be called from within Jinja2 template
    def generate_wrapper(key):
        val = factory.get_value_by_path(key)
        # Fallback if None (though Mappings should cover it, good for debug)
        return val if val is not None else "UNKNOWN"

    for i in range(args.count):
        # Pick a random template
        template = random.choice(templates)
        
        # Context with our generator function
        context = {'gen': generate_wrapper}
        
        # Render
        rendered_xml = template.render(context)
        
        # Save
        filename = f"generated_{i+1:04d}.xml"
        output_path = OUTPUT_DIR / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_xml)
            
    print(f"Successfully generated {args.count} files in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
