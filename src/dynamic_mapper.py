import re

class DynamicMapper:
    def __init__(self):
        # Heuristic rules: (Regex Pattern, DataFactory Key)
        # Order matters — specific patterns must precede general ones.
        self.rules = [
            # --- Identity documents ---
            (r'(?i)CNPJ', 'company.cnpj'),
            (r'(?i)CPF',  'person.cpf'),
            (r'(?i)^IE$', 'company.ie'),      # Exact match: IE alone (not CNPJ-like)

            # --- Company identity ---
            (r'(?i)xFant|NomeFantasia',  'company.fantasy_name'),
            (r'(?i)razSocial',           'company.company_name'),
            (r'(?i)CNAE',               'company.cnae'),
            (r'^IM$',                   'company.im'),
            (r'(?i)xContato',           'company.contact_name'),

            # --- Address fields ---
            (r'(?i)xLgr|Logradouro|xEnder', 'location.street'),
            (r'(?i)^nro$|Numero',            'location.number'),
            (r'(?i)xCpl|Complemento',        'location.complement'),
            (r'(?i)xBairro|Bairro',          'location.district'),
            (r'(?i)xMun|Cidade',             'location.city_name'),
            (r'(?i)^cMun$|^cMunFG$',           'location.city_code'),
            (r'(?i)^UF$|Estado',             'location.state_abbr'),
            (r'(?i)^CEP$',                   'location.postcode'),

            # --- Product / item fields ---
            (r'(?i)xProd|Descricao',        'product.description'),
            (r'(?i)^NCM$',                  'product.ncm'),
            (r'(?i)cEAN|EAN',               'product.ean'),
            (r'(?i)^CEST$',                 'product.cest'),
            (r'(?i)^cProd$',                'product.code'),
            (r'(?i)^qCom$|^qTrib$',         'product.quantity'),
            (r'(?i)^pesoL$|^pesoB$',        'product.weight'),
            (r'(?i)^qVol$',                 'product.qty_int'),
            # Unit prices and product totals (specific before generic v[A-Z])
            (r'(?i)vProd|vUn(?:Com|Trib)|ValorTotal|ValorUnit', 'product.price'),

            # --- Person / contact ---
            (r'(?i)xNome|Nome', 'person.name'),
            (r'(?i)email',      'person.email'),
            (r'(?i)fone|Telefone', 'person.phone'),

            # --- Document-level codes and references ---
            (r'(?i)^nDup$',         'document.dup_number'),
            (r'(?i)idCadIntTran',   'document.intermediator_id'),
            (r'(?i)^xPed$',         'document.order_ref'),
            (r'(?i)^nProt$',        'document.protocol_number'),
            (r'(?i)^dVenc$',        'document.due_date'),
            (r'(?i)^dhEvento$|^dhSaiEnt$', 'document.event_datetime'),
            (r'(?i)^tPag$',         'document.payment_type'),

            # --- Document-level free-text fields ---
            (r'(?i)^infCpl$',  'document.tax_summary'),
            (r'(?i)^xJust$',   'document.cancellation_reason'),

            # --- Monetary totals and amounts (broad catch-all for v[A-Z] tags) ---
            # Specific exclusions (vBCST, vFCP*, vII, vIPI*, vOutro, vSeg, vICMSDeson)
            # are in IGNORE_TAGS and will be skipped before reaching here.
            (r'^v[A-Z]', 'monetary.amount'),

            # --- Tax rates (pCOFINS, pPIS, pFCPUFDest, pICMSUFDest) ---
            # pICMS and pICMSInter/Part are in IGNORE_TAGS; these cover the rest.
            (r'^p[A-Z]', 'monetary.tax_rate'),
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
        from lxml import etree
        mapping = {}
        for element in root.iter():
            if len(element) == 0:
                tag_name = etree.QName(element.tag).localname
                if tag_name not in mapping:
                    inferred_key = self.infer_provider(tag_name, element.text)
                    if inferred_key:
                        mapping[tag_name] = inferred_key
        return mapping
