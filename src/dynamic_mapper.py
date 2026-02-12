import re

class DynamicMapper:
    def __init__(self):
        # Heuristic rules: (Regex Pattern, DataFactory Key)
        # Order matters! Specific patterns should come before general ones.
        self.rules = [
            (r'(?i)CNPJ', 'company.cnpj'),
            (r'(?i)CPF', 'person.cpf'),
            (r'(?i)IE', 'company.ie'),
            (r'(?i)xFant', 'company.fantasy_name'),
            (r'(?i)razSocial', 'company.company_name'),
            
            # Address - Matches both standard NFe tags and generic names
            (r'(?i)xLgr|Logradouro', 'location.street'),
            (r'(?i)nro|Numero', 'location.number'),
            (r'(?i)xBairro|Bairro', 'location.district'),
            (r'(?i)xMun|Cidade', 'location.city_name'),
            (r'(?i)cMun', 'location.city_code'),
            (r'(?i)UF|Estado', 'location.state_abbr'),
            (r'(?i)CEP', 'location.postcode'),
            
            # Product / Fiscal
            (r'(?i)xProd|Descricao', 'product.description'),
            (r'(?i)NCM', 'product.ncm'),
            (r'(?i)cEAN|EAN', 'product.ean'),
            (r'(?i)vProd|ValorTotal|vUn|ValorUnit', 'product.price'),
            
            # Person / Contact
            # 'xNome' is tricky because it could be a person or a company name depending on context.
            # In NFe, xNome is used for both. We default to 'person.name' but if we see known company tags nearby in a real parser we could be smarter.
            # For now, regex only sees the tag name. 
            (r'(?i)xNome|Nome', 'person.name'),
            (r'(?i)email', 'person.email'),
            (r'(?i)fone|Telefone', 'person.phone'),
            
            # General ID/Code fallbacks - use carefully or avoid if too generic
            # (r'(?i)id', '...'), 
        ]

    def infer_provider(self, tag_name, text_content=None):
        """
        Infers the best DataFactory key for a given XML tag.
        Returns None if no rule matches.
        """
        for pattern, key in self.rules:
            if re.search(pattern, tag_name):
                return key
        return None

    def analyze_root(self, root):
        """
        Traverses an XML root element to build a mapping dictionary.
        Returns a dict: { 'TagName': 'data.factory.key' }
        """
        mapping = {}
        # We only care about leaf nodes for data replacement
        for element in root.iter():
            if len(element) == 0: # Leaf node
                tag_name = element.tag.split('}')[-1] # Strip namespace if present
                
                # If we haven't mapped this tag yet, try to infer
                if tag_name not in mapping:
                    inferred_key = self.infer_provider(tag_name, element.text)
                    if inferred_key:
                        mapping[tag_name] = inferred_key
        
        return mapping
