#!/usr/bin/env python3
"""Best-effort n8n workflow JSON redaction. Manual security review REQUIRED.

Usage: python3 scripts/sanitize_n8n_export.py export.json workflows/podcast-daily.json
"""
import json
import re
import sys
from pathlib import Path

SENSITIVE_KEYS = {
    'credentials', 'pinData', 'staticData', 'shared',
    'homeProject', 'ownedBy', 'createdBy', 'updatedBy',
    'authorization', 'apiKey', 'api_key', 'accessToken', 'refreshToken',
    'telegramBotToken', 'botToken', 'bridgeSharedKey',
    'X-Bridge-Key', 'x-bridge-key', 'N8N_ENCRYPTION_KEY',
}

PATTERNS = [
    (re.compile(r'(?i)Bearer\s+[A-Za-z0-9._~+/-]{12,}'), 'Bearer REPLACE_WITH_API_KEY'),
    (re.compile(r'\b\d{8,12}:[A-Za-z0-9_-]{25,}\b'), 'REPLACE_WITH_TELEGRAM_BOT_TOKEN'),
    (re.compile(r'\bsk-[A-Za-z0-9_-]{16,}\b'), 'REPLACE_WITH_API_KEY'),
    (re.compile(r'(?i)(telegramChatId\s*[:=]\s*[\'\"`])(-?\d{6,20})([\'\"`])'), r'\1REPLACE_WITH_TELEGRAM_CHAT_ID\3'),
    (re.compile(r'(?i)(ALLOWED_CHAT_ID\s*=\s*[\'\"]?)(-?\d{6,20})'), r'\1REPLACE_WITH_TELEGRAM_CHAT_ID'),
]


def clean(obj, key=None):
    if isinstance(obj, dict):
        return {k: clean(v, k) for k, v in obj.items()
                if k not in SENSITIVE_KEYS and not (k in ('id', 'versionId') and key == '__workflow_root__')}
    if isinstance(obj, list):
        return [clean(v, key) for v in obj]
    if isinstance(obj, str):
        if key in ('chatId', 'chat_id') and obj.strip().lstrip('-').isdigit():
            return 'REPLACE_WITH_TELEGRAM_CHAT_ID'
        s = obj
        for pattern, repl in PATTERNS:
            s = pattern.sub(repl, s)
        return s
    return obj


def main():
    if len(sys.argv) != 3:
        sys.exit('Usage: sanitize_n8n_export.py INPUT.json OUTPUT.json')
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    obj = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(obj, dict) or 'nodes' not in obj or 'connections' not in obj:
        sys.exit('Expected an n8n workflow JSON with nodes and connections')
    result = clean(obj, '__workflow_root__')
    result.pop('id', None)
    result.pop('versionId', None)
    result.pop('meta', None)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {target}: {len(result.get("nodes", []))} nodes')
    print('WARNING: inspect JavaScript, URLs, authentication headers, IDs, names and screenshots manually before publishing.')

if __name__ == '__main__':
    main()
