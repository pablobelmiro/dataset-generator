from lxml import etree
from src.constants import IGNORE_TAGS, NFE_KEY_TAGS, CONTEXT_OVERRIDES, CONTEXT_BLOCKS
import random

# Tags whose entire subtree must be stripped before template generation.
# These blocks carry real cryptographic material and protocol data that
# are invalid for any synthetically generated document.
STRIP_BLOCKS = {'Signature', 'protNFe', 'retEvento'}

_NS = 'http://www.portalfiscal.inf.br/nfe'


class XMLProcessor:
    def __init__(self):
        pass

    def ingest_xml(self, file_path):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file_path, parser)
        return tree

    def _strip_sensitive_blocks(self, root):
        """
        Removes elements in STRIP_BLOCKS along with their entire subtree.
        Eliminates real digital signatures and SEFAZ authorization protocols.
        """
        for block_name in STRIP_BLOCKS:
            for element in root.iter():
                if etree.QName(element.tag).localname == block_name:
                    parent = element.getparent()
                    if parent is not None:
                        parent.remove(element)

    def create_template(self, tree, mapping):
        """
        Converts an lxml ElementTree into a Jinja2 template string.
        """
        root = tree.getroot()
        self._strip_sensitive_blocks(root)

        for element in root.iter():
            if len(element) > 0:
                continue

            tag_name = etree.QName(element.tag).localname

            if tag_name in IGNORE_TAGS:
                continue

            if tag_name in NFE_KEY_TAGS:
                element.text = f"{{{{ {NFE_KEY_TAGS[tag_name]} }}}}"
                continue

            # Context-aware override: walk ancestors to find the nearest
            # semantic block (emit, dest, transp, …) and use a named entity
            # key that is specific to that block.
            block = self._ancestor_block(element)
            override = CONTEXT_OVERRIDES.get((block, tag_name)) if block else None
            if override:
                element.text = f"{{{{ gen('{override}') }}}}"
                continue

            if tag_name in mapping:
                element.text = f"{{{{ gen('{mapping[tag_name]}') }}}}"

        # Must run after the main loop so it overrides any generic mappings
        # that the DynamicMapper applied to structurally-keyed fields.
        self._replace_nfe_id_attribute(root)

        return etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True).decode('utf-8')

    def _ancestor_block(self, element):
        """Returns the local name of the nearest ancestor in CONTEXT_BLOCKS."""
        parent = element.getparent()
        while parent is not None:
            local = etree.QName(parent.tag).localname
            if local in CONTEXT_BLOCKS:
                return local
            parent = parent.getparent()
        return None

    def detect_document_type(self, tree):
        """
        Returns 'nfe' for a standard NF-e (nfeProc / NFe root) or
        'cancellation' for a cancellation event (procEventoNFe root).
        """
        local = etree.QName(tree.getroot().tag).localname
        if local == 'procEventoNFe':
            return 'cancellation'
        return 'nfe'

    def _replace_nfe_id_attribute(self, root):
        """
        Replaces the Id attribute on <infNFe> / <infEvento> with a Jinja2
        placeholder so the generated key is consistent with structural fields.
        Also fixes the CNPJ inside <infEvento> (cancellation) so it uses the
        same emitter CNPJ that is embedded in the generated access key.
        """
        for element in root.iter():
            local = etree.QName(element.tag).localname
            if local in ('infNFe', 'infEvento') and element.get('Id') is not None:
                element.set('Id', "{{ nfe.id }}")
            # In cancellation events the CNPJ inside <infEvento> refers to the
            # emitter of the cancelled NF-e — it must match the CNPJ embedded
            # in the access key.
            if local == 'infEvento':
                for child in element:
                    if etree.QName(child.tag).localname == 'CNPJ':
                        child.text = "{{ nfe.cnpj }}"

    # ------------------------------------------------------------------
    # Problem 5: post-render financial consistency pass
    # ------------------------------------------------------------------

    def post_process_financial(self, xml_string):
        """
        Parses a fully-rendered NF-e XML and fixes mathematical inconsistencies:
        - Per item: vProd = qCom × vUnCom; qTrib = qCom; vUnTrib = vUnCom
        - Per item taxes: vBC = vProd; vICMS, vPIS, vCOFINS recalculated
        - Totals (ICMSTot): aggregated from corrected item values
        - Billing (cobr/fat, dup): aligned with vNF
        - Payment (detPag): vPag aligned with vNF
        Documents without <det> blocks (e.g. cancellation events) are
        returned unchanged.
        """
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(xml_string.encode(), parser)
        except etree.XMLSyntaxError:
            return xml_string

        det_list = root.findall(f'.//{{{_NS}}}det')
        if not det_list:
            return xml_string

        items = [self._fix_item_financials(det) for det in det_list]

        vFrete = round(random.uniform(5, 50), 2) if random.random() < 0.25 else 0.0
        vDesc  = round(random.uniform(1, 30), 2) if random.random() < 0.15 else 0.0

        total_vProd = round(sum(i['vProd'] for i in items), 2)
        vNF = round(total_vProd + vFrete - vDesc, 2)

        totals = {
            'vProd':          total_vProd,
            'vBC':            round(sum(i['vBC_icms'] for i in items), 2),
            'vICMS':          round(sum(i['vICMS'] for i in items), 2),
            'vPIS':           round(sum(i['vPIS'] for i in items), 2),
            'vCOFINS':        round(sum(i['vCOFINS'] for i in items), 2),
            'vFCPUFDest':     round(sum(i.get('vFCPUFDest', 0) for i in items), 2),
            'vICMSUFDest':    round(sum(i.get('vICMSUFDest', 0) for i in items), 2),
            'vTotTrib':       round(sum(i['vTotTrib'] for i in items), 2),
            # Always zero for standard (non-ST) NF-e operations
            'vST':            0.0,
            'vICMSUFRemet':   0.0,
            'vFrete': vFrete,
            'vDesc':  vDesc,
            'vNF':    vNF,
        }

        self._update_icmstot(root, totals)
        self._update_billing(root, totals)
        self._update_payment(root, vNF)

        return etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True).decode('utf-8')

    def _fix_item_financials(self, det):
        """Regenerates consistent financial values for one <det> block."""
        result = {'vProd': 0, 'vBC_icms': 0, 'vICMS': 0,
                  'vPIS': 0, 'vCOFINS': 0, 'vTotTrib': 0}

        prod = det.find(f'{{{_NS}}}prod')
        if prod is None:
            return result

        qty        = round(random.uniform(1.0, 20.0), 4)
        unit_price = round(random.uniform(5.0, 500.0), 2)
        vProd      = round(qty * unit_price, 2)

        for tag, val in [
            ('qCom',    f'{qty:.4f}'),
            ('vUnCom',  f'{unit_price:.2f}'),
            ('vProd',   f'{vProd:.2f}'),
            ('qTrib',   f'{qty:.4f}'),
            ('vUnTrib', f'{unit_price:.2f}'),
        ]:
            self._set(prod, tag, val)

        result['vProd'] = vProd
        result['vBC_icms'] = vProd

        imposto = det.find(f'{{{_NS}}}imposto')
        if imposto is None:
            return result

        vICMS = vPIS = vCOFINS = 0.0
        vFCPUFDest = vICMSUFDest = 0.0

        # --- ICMS ---
        icms_el = imposto.find(f'{{{_NS}}}ICMS')
        if icms_el is not None:
            for regime in list(icms_el):
                pICMS = self._read_float(regime, 'pICMS') or 4.0
                vICMS = round(vProd * pICMS / 100, 2)
                self._set(regime, 'vBC',   f'{vProd:.2f}')
                self._set(regime, 'vICMS', f'{vICMS:.2f}')
                break   # only one regime per item

        # --- PIS ---
        pis_block = imposto.find(f'{{{_NS}}}PIS')
        if pis_block is not None:
            pPIS_el = pis_block.find(f'.//{{{_NS}}}pPIS')
            pPIS = float(pPIS_el.text) if (pPIS_el is not None and pPIS_el.text) else 1.65
            vPIS = round(vProd * pPIS / 100, 2)
            vBC_el = pis_block.find(f'.//{{{_NS}}}vBC')
            if vBC_el is not None:
                vBC_el.text = f'{vProd:.2f}'
            vPIS_el = pis_block.find(f'.//{{{_NS}}}vPIS')
            if vPIS_el is not None:
                vPIS_el.text = f'{vPIS:.2f}'

        # --- COFINS ---
        cofins_block = imposto.find(f'{{{_NS}}}COFINS')
        if cofins_block is not None:
            pCOFINS_el = cofins_block.find(f'.//{{{_NS}}}pCOFINS')
            pCOFINS = float(pCOFINS_el.text) if (pCOFINS_el is not None and pCOFINS_el.text) else 7.60
            vCOFINS = round(vProd * pCOFINS / 100, 2)
            vBC_el = cofins_block.find(f'.//{{{_NS}}}vBC')
            if vBC_el is not None:
                vBC_el.text = f'{vProd:.2f}'
            vCOFINS_el = cofins_block.find(f'.//{{{_NS}}}vCOFINS')
            if vCOFINS_el is not None:
                vCOFINS_el.text = f'{vCOFINS:.2f}'

        # --- ICMSUFDest (DIFAL for interstate sales) ---
        difal = imposto.find(f'{{{_NS}}}ICMSUFDest')
        if difal is not None:
            pICMSUFDest = self._read_float(difal, 'pICMSUFDest') or 18.0
            pICMSInter  = self._read_float(difal, 'pICMSInter')  or 4.0
            pFCPUFDest  = self._read_float(difal, 'pFCPUFDest')  or 0.0

            vFCPUFDest  = round(vProd * pFCPUFDest / 100, 2)
            vICMSUFDest = round(vProd * (pICMSUFDest - pICMSInter) / 100, 2)

            self._set(difal, 'vBCUFDest',    f'{vProd:.2f}')
            self._set(difal, 'vBCFCPUFDest', f'{vProd:.2f}')
            self._set(difal, 'vFCPUFDest',   f'{vFCPUFDest:.2f}')
            self._set(difal, 'vICMSUFDest',  f'{vICMSUFDest:.2f}')
            self._set(difal, 'vICMSUFRemet', '0.00')

        vTotTrib = round(vICMS + vPIS + vCOFINS, 2)
        self._set(imposto, 'vTotTrib', f'{vTotTrib:.2f}')

        result.update({
            'vICMS': vICMS, 'vPIS': vPIS, 'vCOFINS': vCOFINS,
            'vFCPUFDest': vFCPUFDest, 'vICMSUFDest': vICMSUFDest,
            'vTotTrib': vTotTrib,
        })
        return result

    def _update_icmstot(self, root, totals):
        icmstot = root.find(f'.//{{{_NS}}}ICMSTot')
        if icmstot is None:
            return
        for tag, val in totals.items():
            el = icmstot.find(f'{{{_NS}}}{tag}')
            if el is not None:
                el.text = f'{val:.2f}'

    def _update_billing(self, root, totals):
        vNF  = totals['vNF']
        vDesc = totals['vDesc']
        vLiq = round(vNF - vDesc, 2)

        fat = root.find(f'.//{{{_NS}}}fat')
        if fat is not None:
            self._set(fat, 'vOrig', f'{vNF:.2f}')
            self._set(fat, 'vDesc', f'{vDesc:.2f}')
            self._set(fat, 'vLiq',  f'{vLiq:.2f}')

        dups = root.findall(f'.//{{{_NS}}}dup')
        if dups:
            per_dup = round(vLiq / len(dups), 2)
            for dup in dups:
                self._set(dup, 'vDup', f'{per_dup:.2f}')

    def _update_payment(self, root, vNF):
        detpag_list = root.findall(f'.//{{{_NS}}}detPag')
        if not detpag_list:
            return
        per_pag = round(vNF / len(detpag_list), 2)
        for detpag in detpag_list:
            self._set(detpag, 'vPag', f'{per_pag:.2f}')

    def _set(self, parent, local_tag, value):
        """Set text of a direct or descendant child by local tag name."""
        el = parent.find(f'{{{_NS}}}{local_tag}')
        if el is not None:
            el.text = value

    def _read_float(self, parent, local_tag):
        el = parent.find(f'{{{_NS}}}{local_tag}')
        if el is not None and el.text:
            try:
                return float(el.text)
            except ValueError:
                pass
        return None
