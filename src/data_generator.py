from faker import Faker
import random

class DataFactory:
    def __init__(self, locale='pt_BR'):
        self.fake = Faker(locale)
    
    def generate_person(self):
        """Generates person data."""
        return {
            'name': self.fake.name(),
            'cpf': self.fake.cpf(),
            'rg': self.fake.rg(),
            'phone': self.fake.phone_number(),
            'email': self.fake.email()
        }

    def generate_company(self):
        """Generates company data."""
        return {
            'company_name': self.fake.company(),
            'fantasy_name': self.fake.company_mode() if hasattr(self.fake, 'company_mode') else self.fake.company(),
            'cnpj': self.fake.cnpj(),
            'ie': self.fake.random_number(digits=9, fix_len=True) # Basic IE simulation
        }

    def generate_location(self):
        """Generates location data."""
        # Note: Faker's address provider might return random cities/states. 
        # For consistency, we might want to generate a full address block.
        return {
            'street': self.fake.street_name(),
            'number': str(self.fake.random_number(digits=3)),
            'district': self.fake.bairro(),
            'city_name': self.fake.city(),
            'city_code': str(self.fake.random_number(digits=7, fix_len=True)), # IBGE code simulation
            'state_abbr': self.fake.state_abbr(),
            'postcode': self.fake.postcode()
        }

    def generate_product(self):
        """Generates product data."""
        price = round(random.uniform(10.0, 1000.0), 2)
        return {
            'description': self.fake.catch_phrase(), # Using catch_phrase for product desc simulation
            'ean': self.fake.ean13(),
            'ncm': str(self.fake.random_number(digits=8, fix_len=True)),
            'price': f"{price:.2f}"
        }

    def get_value_by_path(self, path):
        """Resolves 'category.field' paths to actual generated values."""
        category, field = path.split('.')
        
        # We need to maintain context state for the current entity being generated 
        # (e.g., if we access person.name then person.cpf, it should be the same person).
        # However, purely random generation for each tag is simpler for now unless 
        # consistency is strictly required across tags in the same block. 
        # Given the requirement for "realistic", let's assume valid pairs (CPF matches Name) 
        # are nice but structure is key. 
        # OPTIMIZATION: To ensure consistency (e.g. valid address block), we should probably 
        # generate the whole object once and cache it for the current 'row' or 'iteration'?
        # For this implementation, I will generate fresh data on call, 
        # but I will implement a caching mechanism in the main loop if needed.
        
        # Actually, let's generate fresh for each call for simplicity, 
        # as complex state management inside DataFactory for XML tree traversal is tricky.
        
        if category == 'person':
            return self.generate_person().get(field)
        elif category == 'company':
            return self.generate_company().get(field)
        elif category == 'location':
            return self.generate_location().get(field)
        elif category == 'product':
            return self.generate_product().get(field)
        
        return None
