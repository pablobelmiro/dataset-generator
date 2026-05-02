# Tags that should NOT be touched (static data or controlled by logic)
IGNORE_TAGS = [
    # Protocol / version metadata
    'versao', 'natOp', 'mod', 'dhEmi',
    'tpNF', 'idDest', 'tpImp', 'tpEmis', 'tpAmb',
    'finNFe', 'indFinal', 'indPres', 'procEmi', 'verProc',
    # Fiscal classification codes (structural, not PII)
    'orig', 'CST', 'modBC', 'pICMS', 'indTot',
    'CFOP', 'CRT',
    # Interstate ICMS rates (come from fiscal law, not from the document entity)
    'pICMSInter', 'pICMSInterPart',
    # Always-constant values in Brazilian NF-e
    'cPais', 'xPais',       # 1058 / Brasil
    # Unit / measure / indicator flags (enum, not PII)
    'uCom', 'uTrib', 'indEscala', 'modFrete',
    'indIntermed', 'indPag',
    # Cancellation-event fixed values
    'tpEvento', 'nSeqEvento', 'verEvento', 'descEvento',
    # Monetary fields that are structurally zero in standard NF-e operations
    # and therefore carry no information about the real transaction
    'vBCST', 'vFCP', 'vFCPST', 'vFCPSTRet',
    'vII', 'vIPI', 'vIPIDevol', 'vOutro', 'vICMSDeson', 'vSeg',
    # Volume/packaging descriptor (e.g. "Pacote(s)") — structural
    'esp',
    # Destination IE indicator enum (0=contribuinte, 1=isento, 9=não contribuinte)
    'indIEDest',
    # Sequential item counter in the purchase order — not sensitive
    'nItemPed',
]

# Fields that are components of the NF-e access key.
# They must all be derived from the same generated key to ensure structural
# consistency: cDV is a module-11 check digit over the other 43 digits, and
# the key itself embeds the emitter CNPJ, serie, nNF, etc.
NFE_KEY_TAGS = {
    'cUF':   'nfe.cUF',
    'cNF':   'nfe.cNF',
    'nNF':   'nfe.nNF',
    'serie': 'nfe.serie',
    'cDV':   'nfe.cDV',
    # Invoice / billing number mirrors the NF number
    'nFat':  'nfe.nFat',
    # The 44-digit key referenced in cancellation events
    'chNFe': 'nfe.key',
    # State code of the authorizing body (cancellation events) — same as cUF
    'cOrgao': 'nfe.cUF',
}

# Ancestor-block-aware overrides for create_template().
# Key: (ancestor_block_local_name, leaf_tag_local_name)
# Value: DataFactory path — uses named entity categories (emit_company,
# dest_person, dest_location, etc.) so each logical entity is coherent
# and emit / dest refer to genuinely different pre-generated objects.
CONTEXT_OVERRIDES = {
    # --- Emitter (always a legal entity / company) ---
    ('emit', 'xNome'):   'emit_company.company_name',
    ('emit', 'xFant'):   'emit_company.fantasy_name',
    ('emit', 'CNPJ'):    'emit_company.cnpj',
    ('emit', 'IE'):      'emit_company.ie',
    ('emit', 'IM'):      'emit_company.im',
    ('emit', 'CNAE'):    'emit_company.cnae',
    ('emit', 'fone'):    'emit_company.phone',
    ('emit', 'email'):   'emit_company.email',
    # Emitter address
    ('emit', 'xLgr'):    'emit_location.street',
    ('emit', 'nro'):     'emit_location.number',
    ('emit', 'xCpl'):    'emit_location.complement',
    ('emit', 'xBairro'): 'emit_location.district',
    ('emit', 'xMun'):    'emit_location.city_name',
    ('emit', 'CEP'):     'emit_location.postcode',

    # --- Recipient (person for CPF-based, company for CNPJ-based) ---
    ('dest', 'xNome'):   'dest_person.name',
    ('dest', 'CPF'):     'dest_person.cpf',
    ('dest', 'CNPJ'):    'dest_company.cnpj',
    ('dest', 'fone'):    'dest_person.phone',
    ('dest', 'email'):   'dest_person.email',
    # Recipient address
    ('dest', 'xLgr'):    'dest_location.street',
    ('dest', 'nro'):     'dest_location.number',
    ('dest', 'xCpl'):    'dest_location.complement',
    ('dest', 'xBairro'): 'dest_location.district',
    ('dest', 'xMun'):    'dest_location.city_name',
    ('dest', 'CEP'):     'dest_location.postcode',

    # --- Auxiliary parties (transport, authorized downloader, tech contact) ---
    ('autXML',      'CNPJ'):    'aux_company.cnpj',
    ('infRespTec',  'CNPJ'):    'aux_company.cnpj',
    ('infRespTec',  'xContato'):'aux_company.company_name',
    ('infRespTec',  'fone'):    'aux_company.phone',
    ('infRespTec',  'email'):   'aux_company.email',
    ('infIntermed', 'CNPJ'):    'aux_company.cnpj',
    ('transp',      'xNome'):   'aux_company.company_name',
    ('transp',      'CNPJ'):    'aux_company.cnpj',
}

# Ancestor blocks that define a semantic context for their descendants.
CONTEXT_BLOCKS = frozenset({
    'emit', 'dest', 'transp', 'autXML',
    'infRespTec', 'infIntermed', 'det',
    'cobr', 'pag', 'infAdic', 'total',
})
