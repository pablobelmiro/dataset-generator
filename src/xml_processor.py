from lxml import etree
from src.constants import IGNORE_TAGS

class XMLProcessor:
    def __init__(self):
        pass

    def ingest_xml(self, file_path):
        """
        Reads an XML file and returns the root element.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file_path, parser)
        return tree

    def create_template(self, tree, mapping):
        """
        Converts an lxml ElementTree into a Jinja2 template string.
        Replaces known tags with Jinja2 expressions calling a generator function.
        Uses a dynamic mapping dictionary passed at runtime.
        """
        root = tree.getroot()
        
        # We need to iterate over all elements
        for element in root.iter():
            # Skip if it has children, we only want to replace leaf node text
            if len(element) > 0:
                continue
                
            # Strip namespaces for the mapping lookup to be easier
            tag_name = etree.QName(element.tag).localname
            
            if tag_name in IGNORE_TAGS:
                continue
                
            if tag_name in mapping:
                mapping_key = mapping[tag_name]
                # Replace text with Jinja2 expression
                # We use a custom function 'gen' injected into the template context
                element.text = f"{{{{ gen('{mapping_key}') }}}}"
        
        # Convert back to string
        # decode to ensure we return a string, not bytes
        return etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True).decode('utf-8')
