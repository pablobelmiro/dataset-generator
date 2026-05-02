from faker import Faker
from datetime import datetime, timedelta
from itertools import cycle
import random
import re

# Curated table of real Brazilian municipalities.
# Each row: (cMun, xMun, UF, cUF, cep_prefix_5digits)
# cMun = IBGE 7-digit code; cUF = IBGE state code (2 digits).
# CEP suffix (3 digits) is generated randomly to avoid reusing real postcodes.
_MUNICIPIOS = [
    # SP
    ('3550308', 'Sao Paulo',              'SP', '35', '01310'),
    ('3509502', 'Campinas',               'SP', '35', '13010'),
    ('3547809', 'Ribeirao Preto',         'SP', '35', '14010'),
    ('3548708', 'Santos',                 'SP', '35', '11010'),
    ('3518800', 'Guarulhos',              'SP', '35', '07010'),
    ('3529401', 'Osasco',                 'SP', '35', '06010'),
    ('3543402', 'Piracicaba',             'SP', '35', '13400'),
    ('3513801', 'Diadema',                'SP', '35', '09910'),
    # RJ
    ('3304557', 'Rio de Janeiro',         'RJ', '33', '20010'),
    ('3303500', 'Niteroi',                'RJ', '33', '24010'),
    ('3302858', 'Nova Iguacu',            'RJ', '33', '26010'),
    ('3301702', 'Duque de Caxias',        'RJ', '33', '25010'),
    # MG
    ('3106200', 'Belo Horizonte',         'MG', '31', '30110'),
    ('3170206', 'Uberlandia',             'MG', '31', '38400'),
    ('3136702', 'Juiz de Fora',           'MG', '31', '36010'),
    ('3143302', 'Montes Claros',          'MG', '31', '39400'),
    # ES
    ('3205309', 'Vitoria',                'ES', '32', '29010'),
    ('3205002', 'Serra',                  'ES', '32', '29160'),
    ('3201308', 'Cariacica',              'ES', '32', '29140'),
    ('3205200', 'Vila Velha',             'ES', '32', '29100'),
    # BA
    ('2927408', 'Salvador',               'BA', '29', '40010'),
    ('2910800', 'Feira de Santana',       'BA', '29', '44001'),
    ('2933307', 'Vitoria da Conquista',   'BA', '29', '45010'),
    # PE
    ('2611606', 'Recife',                 'PE', '26', '50010'),
    ('2607901', 'Jaboatao dos Guararapes','PE', '26', '54310'),
    ('2604106', 'Caruaru',                'PE', '26', '55010'),
    # CE
    ('2304400', 'Fortaleza',              'CE', '23', '60110'),
    ('2307650', 'Sobral',                 'CE', '23', '62010'),
    # MA
    ('2111300', 'Sao Luis',               'MA', '21', '65010'),
    ('2105302', 'Imperatriz',             'MA', '21', '65900'),
    # PA
    ('1501402', 'Belem',                  'PA', '15', '66010'),
    ('1502400', 'Ananindeua',             'PA', '15', '67000'),
    # AM
    ('1302603', 'Manaus',                 'AM', '13', '69010'),
    # PR
    ('4106902', 'Curitiba',               'PR', '41', '80010'),
    ('4113700', 'Londrina',               'PR', '41', '86010'),
    ('4115200', 'Maringa',                'PR', '41', '87010'),
    ('4118402', 'Ponta Grossa',           'PR', '41', '84010'),
    # SC
    ('4205407', 'Florianopolis',          'SC', '42', '88010'),
    ('4202404', 'Blumenau',               'SC', '42', '89010'),
    ('4218707', 'Sao Jose',               'SC', '42', '88101'),
    ('4209102', 'Joinville',              'SC', '42', '89201'),
    # RS
    ('4314902', 'Porto Alegre',           'RS', '43', '90010'),
    ('4309209', 'Caxias do Sul',          'RS', '43', '95010'),
    ('4304606', 'Canoas',                 'RS', '43', '92010'),
    ('4316907', 'Santa Maria',            'RS', '43', '97010'),
    # GO
    ('5208707', 'Goiania',                'GO', '52', '74010'),
    ('5201405', 'Aparecida de Goiania',   'GO', '52', '74910'),
    # DF
    ('5300108', 'Brasilia',               'DF', '53', '70010'),
    # MS
    ('5002704', 'Campo Grande',           'MS', '50', '79010'),
    # MT
    ('5103403', 'Cuiaba',                 'MT', '51', '78010'),
    # RN
    ('2408102', 'Natal',                  'RN', '24', '59010'),
    # PB
    ('2507507', 'Joao Pessoa',            'PB', '25', '58010'),
    # AL
    ('2704302', 'Maceio',                 'AL', '27', '57010'),
    # SE
    ('2800308', 'Aracaju',                'SE', '28', '49010'),
    # PI
    ('2211001', 'Teresina',               'PI', '22', '64010'),
    # TO
    ('1721000', 'Palmas',                 'TO', '17', '77010'),
    # RO
    ('1100205', 'Porto Velho',            'RO', '11', '76801'),
    # AC
    ('1200401', 'Rio Branco',             'AC', '12', '69901'),
    # RR
    ('1400100', 'Boa Vista',              'RR', '14', '69301'),
    # AP
    ('1600303', 'Macapa',                 'AP', '16', '68901'),
]

# Valid CFOP codes commonly used in NF-e (sales)
_CFOP_CODES = [
    '5101', '5102', '5103', '5104', '5401', '5405',
    '6101', '6102', '6103', '6108', '6401', '6404',
]

# Common payment type codes (tPag) per SEFAZ table
_TPAG_CODES = ['01', '02', '03', '04', '05', '10', '11', '12', '13', '15', '90', '99']

class DataFactory:
    def __init__(self, locale='pt_BR'):
        self.fake = Faker(locale)

    def generate_person(self):
        return {
            'name': self.fake.name(),
            'cpf': self.fake.cpf(),
            'rg': self.fake.rg(),
            'phone': self.fake.phone_number(),
            'email': self.fake.email(),
        }

    def generate_company(self):
        return {
            'company_name': self.fake.company(),
            'fantasy_name': self.fake.company(),
            'cnpj': self.fake.cnpj(),
            'ie': str(self.fake.random_number(digits=9, fix_len=True)),
            'cnae': str(self.fake.random_number(digits=7, fix_len=True)),
            'im': str(self.fake.random_number(digits=7, fix_len=True)),
            'contact_name': self.fake.company(),
        }

    def generate_location(self):
        """
        Generates a geographically consistent address block.
        Municipality, state abbreviation, IBGE code, and CEP prefix all come
        from the same row of the curated _MUNICIPIOS table so they refer to
        the same real Brazilian city.  Only street-level fields (logradouro,
        number, complement, bairro) are generated independently by Faker.
        """
        cMun, xMun, uf, cuf, cep_prefix = random.choice(_MUNICIPIOS)
        cep_suffix = str(random.randint(0, 999)).zfill(3)
        postcode = f'{cep_prefix}{cep_suffix}'
        return {
            'street':      self.fake.street_name(),
            'number':      str(self.fake.random_int(1, 9999)),
            'complement':  self._address_complement(),
            'district':    self.fake.bairro(),
            'city_name':   xMun,
            'city_code':   cMun,
            'state_abbr':  uf,
            'postcode':    postcode,
        }

    def generate_product(self):
        qty = round(random.uniform(1.0, 100.0), 4)
        unit_price = round(random.uniform(1.0, 500.0), 2)
        return {
            'description': self.fake.catch_phrase(),
            'ean': self.fake.ean13(),
            'ncm': str(self.fake.random_number(digits=8, fix_len=True)),
            'cest': str(self.fake.random_number(digits=7, fix_len=True)),
            'code': self.fake.bothify(text='???####').upper(),
            'cfop': random.choice(_CFOP_CODES),
            'price': f"{unit_price:.2f}",
            'quantity': f"{qty:.4f}",
            'weight': f"{round(random.uniform(0.05, 50.0), 3):.3f}",
            'qty_int': str(random.randint(1, 20)),
        }

    def generate_monetary(self):
        amount = round(random.uniform(0.01, 5000.0), 2)
        tax_amount = round(amount * random.uniform(0.01, 0.3), 2)
        return {
            'amount': f"{amount:.2f}",
            'tax_amount': f"{tax_amount:.2f}",
            'tax_rate': f"{round(random.uniform(0.65, 12.0), 2):.2f}",
        }

    def generate_document(self):
        fed_pct = round(random.uniform(5.0, 20.0), 2)
        est_pct = round(random.uniform(3.0, 18.0), 2)
        total_pct = round(fed_pct + est_pct, 2)
        total_val = round(random.uniform(5.0, 500.0), 2)
        fed_val = round(total_val * fed_pct / total_pct, 2)
        est_val = round(total_val - fed_val, 2)
        tax_summary = (
            f"Total aproximado de tributos: R$ {total_val:.2f} ({total_pct:.2f}%)"
            f"  Federais R$ {fed_val:.2f} ({fed_pct:.2f}%)"
            f"  Estaduais R$ {est_val:.2f} ({est_pct:.2f}%). Fonte IBPT."
        )
        cancellation_reasons = [
            "Pedido cancelado pelo cliente",
            "Erro na emissao da nota fiscal",
            "Produto indisponivel em estoque",
            "Divergencia nos dados do destinatario",
            "Solicitacao de cancelamento dentro do prazo",
        ]
        due = datetime.now() + timedelta(days=random.randint(1, 60))
        event_dt = datetime.now() - timedelta(hours=random.randint(0, 72))
        protocol_num = str(random.randint(100_000_000_000_000, 999_999_999_999_999))
        return {
            'tax_summary': tax_summary,
            'cancellation_reason': random.choice(cancellation_reasons),
            'due_date': due.strftime('%Y-%m-%d'),
            'event_datetime': event_dt.strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'protocol_number': protocol_num,
            'dup_number': str(random.randint(1, 999)).zfill(3),
            'intermediator_id': str(random.randint(100_000_000, 999_999_999)),
            'order_ref': self.fake.bothify(text='?##?##?').upper(),
            'payment_type': random.choice(_TPAG_CODES),
        }

    def _address_complement(self):
        templates = [
            lambda: f"Apto {self.fake.random_int(1, 400)}",
            lambda: f"Casa {self.fake.random_int(1, 50)}",
            lambda: f"Sala {self.fake.random_int(1, 200)}",
            lambda: f"Bloco {random.choice('ABCDEFGH')} Apto {self.fake.random_int(1, 200)}",
            lambda: f"Galpao {random.choice('ABCDE')}",
            lambda: f"{self.fake.random_int(1, 10)}o andar",
            lambda: f"Loja {self.fake.random_int(1, 30)}",
        ]
        return random.choice(templates)()

    def _calc_nfe_check_digit(self, key_43):
        """Module-11 check digit over the 43-digit NF-e key (without cDV)."""
        weights = cycle(range(2, 10))
        total = sum(int(d) * w for d, w in zip(reversed(key_43), weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    def generate_nfe_key(self):
        """
        Generates a complete, internally consistent NF-e access key.
        All structural key fields (cUF, cNF, nNF, serie, cDV, Id attribute,
        nFat, chNFe) derive from this single dict so they are mutually consistent.
        """
        cnpj_raw = re.sub(r'\D', '', self.fake.cnpj())
        cuf = str(random.choice([
            11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29,
            31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53
        ]))
        aamm = datetime.now().strftime('%y%m')
        mod = '55'
        serie = str(random.randint(1, 3)).zfill(3)
        nnf = str(random.randint(1, 999_999_999)).zfill(9)
        tpemis = '1'
        cnf = str(random.randint(10_000_000, 99_999_999))
        key_43 = cuf + aamm + cnpj_raw + mod + serie + nnf + tpemis + cnf
        cdv = str(self._calc_nfe_check_digit(key_43))
        full_key = key_43 + cdv
        nnf_int = str(int(nnf))
        return {
            'id':    f'NFe{full_key}',
            'key':   full_key,          # 44-digit key without "NFe" prefix (for chNFe)
            'cUF':   cuf,
            'cnpj':  cnpj_raw,
            'nNF':   nnf_int,
            'serie': str(int(serie)),
            'cNF':   cnf,
            'cDV':   cdv,
            'nFat':  nnf_int.zfill(6),  # billing invoice number mirrors nNF
        }

    # ------------------------------------------------------------------
    # Document-level entity cache (Problems 7 + 8)
    # ------------------------------------------------------------------

    def new_document_context(self):
        """
        Pre-generates one named snapshot per logical entity role in the
        document.  Named categories (emit_company, dest_person, etc.) map
        directly to the semantic blocks defined in CONTEXT_OVERRIDES so that
        emit and dest always refer to genuinely different pre-generated
        objects and every field within the same block is internally coherent.
        """
        self._entities = {
            # Emitter — always a legal entity
            'emit_company':  self.generate_company(),
            'emit_location': self.generate_location(),
            # Recipient — person (CPF) or company (CNPJ)
            'dest_person':   self.generate_person(),
            'dest_company':  self.generate_company(),
            'dest_location': self.generate_location(),
            # Auxiliary parties (transport, autXML, infRespTec, infIntermed)
            'aux_company':   self.generate_company(),
            # Generic fallbacks for tags not covered by CONTEXT_OVERRIDES
            'person':        self.generate_person(),
            'company':       self.generate_company(),
            'location':      self.generate_location(),
            'document':      self.generate_document(),
        }

    def get_value_by_path(self, path):
        """
        Resolves 'category.field' paths to generated values.
        Named entity categories (emit_company, dest_person, …) return values
        from their dedicated snapshot so all fields within the same XML block
        are coherent.  Product and monetary are generated fresh each call to
        maximise item-level variability across <det> blocks.
        """
        parts = path.split('.', 1)
        if len(parts) != 2:
            return None
        category, field = parts

        if category == 'product':
            return self.generate_product().get(field)
        if category == 'monetary':
            return self.generate_monetary().get(field)

        entities = getattr(self, '_entities', None)
        if entities and category in entities:
            return entities[category].get(field)

        # Fallback: no context — generate on the fly
        _base = category.split('_')[-1]  # strip role prefix (emit_, dest_, aux_)
        _generators = {
            'person':   self.generate_person,
            'company':  self.generate_company,
            'location': self.generate_location,
            'document': self.generate_document,
        }
        gen = _generators.get(_base)
        return gen().get(field) if gen else None
