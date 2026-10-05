#!/usr/bin/env python3
"""Reemplaza datos de infraestructura de un workflow de n8n por placeholders.

Uso:
    python sanitizar_workflow.py workflow.json workflow.sanitized.json
"""
import json, re, sys

# Reemplazos genéricos sobre el texto del JSON (no contienen datos de ningún cliente)
REEMPLAZOS_TEXTO = [
    (r'\bapp[A-Za-z0-9]{14}\b(?<!appendAttribution)', 'TU_AIRTABLE_BASE_ID'),
    (r'\btbl[A-Za-z0-9]{14}\b', 'TU_AIRTABLE_TABLE_ID'),
    (r'[a-f0-9]{64}@group\.calendar\.google\.com', 'TU_CALENDAR_ID@group.calendar.google.com'),
    (r'\b[A-Za-z0-9._%+-]+@gmail\.com\b', 'clinica@ejemplo.com'),
    (r'"phoneNumberId": "\d+"', '"phoneNumberId": "TU_PHONE_NUMBER_ID"'),
]


def limpiar_recursivo(obj):
    """Anonimiza el nombre de la base de Airtable guardado en el caché de n8n."""
    if isinstance(obj, dict):
        url = obj.get('cachedResultUrl')
        if isinstance(url, str) and re.fullmatch(r'https://airtable\.com/app\w+', url):
            obj['cachedResultName'] = 'Base de Airtable'
        for v in obj.values():
            limpiar_recursivo(v)
    elif isinstance(obj, list):
        for v in obj:
            limpiar_recursivo(v)


def limpiar(wf):
    wf.get('meta', {}).pop('instanceId', None)
    for n in wf['nodes']:
        n.pop('webhookId', None)
        for tipo, cred in (n.get('credentials') or {}).items():
            cred['id'] = 'REEMPLAZAR_CREDENCIAL_ID'
            cred['name'] = tipo  # nombre genérico: el tipo de credencial
    limpiar_recursivo(wf)
    return wf


def main(src, dst):
    wf = limpiar(json.load(open(src, encoding='utf-8')))
    txt = json.dumps(wf, ensure_ascii=False, indent=2)
    for patron, nuevo in REEMPLAZOS_TEXTO:
        txt = re.sub(patron, nuevo, txt)
    open(dst, 'w', encoding='utf-8').write(txt)
    json.loads(txt)  # valida que siga siendo JSON válido
    print(f'OK -> {dst}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
