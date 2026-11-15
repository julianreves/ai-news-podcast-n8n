"""Puente local para un workflow n8n Docker -> Kokoro MLX (macOS) -> Telegram sendVoice.

Uso previsto:
  - Kokoro escuchando SOLO en 127.0.0.1:8765
  - Este bridge en 0.0.0.0:8766 para Docker Desktop; proteger puerto con firewall local.
  - n8n usa http://host.docker.internal:8766/render-and-send (Header Auth X-Bridge-Key)

Variables requeridas:
  TELEGRAM_BOT_TOKEN  Token de BotFather, no poner dentro del JSON.
  BRIDGE_SHARED_KEY   Clave fuerte, mínimo 24 caracteres.
  ALLOWED_CHAT_ID    Chat ID al que se permite enviar voz.

Opcionales:
  KOKORO_ENDPOINT    default http://127.0.0.1:8765/v1/audio/speech
  BRIDGE_BIND        default 0.0.0.0
  BRIDGE_PORT        default 8766
  BRIDGE_STATE_FILE  default ~/.kokoro-server/voice_delivery_state.json

Ejecutar: python3 kokoro_bridge.py
Requiere ffmpeg en PATH. Compatible con Python 3.11+; usa solo librería estándar.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

KOKORO = os.environ.get('KOKORO_ENDPOINT', 'http://127.0.0.1:8765/v1/audio/speech')
KEY = os.environ.get('BRIDGE_SHARED_KEY', '')
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT = os.environ.get('ALLOWED_CHAT_ID', '')
HOST = os.environ.get('BRIDGE_BIND', '0.0.0.0')
PORT = int(os.environ.get('BRIDGE_PORT', '8766'))
STATE_FILE = Path(os.environ.get('BRIDGE_STATE_FILE', str(Path.home() / '.kokoro-server/voice_delivery_state.json'))).expanduser()
LOCK = threading.Lock()
MAX_SCRIPT = 38_000
MAX_REQUEST_BYTES = 100_000


def split_sentences(text: str, max_chars: int = 650) -> list[str]:
    units = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    result, carry = [], ''
    for unit in units:
        unit = unit.strip()
        if not unit:
            continue
        while len(unit) > max_chars:
            cut = unit.rfind(' ', 0, max_chars + 1)
            if cut < max_chars // 3:
                cut = max_chars
            head, unit = unit[:cut].strip(), unit[cut:].strip()
            if carry:
                result.append(carry)
                carry = ''
            if head:
                result.append(head)
        if not unit:
            continue
        if carry and len(carry) + len(unit) + 1 > max_chars:
            result.append(carry)
            carry = ''
        carry = (carry + ' ' + unit).strip()
    if carry:
        result.append(carry)
    return result


def generate_wav(text: str, voice: str, target: Path):
    req = Request(KOKORO,
        data=json.dumps({'model':'mlx-community/Kokoro-82M-bf16','input':text,'voice':voice,
                         'lang_code':'e','speed':1.0,'response_format':'wav'}, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=360) as response:
        result=response.read()
    if len(result)<100 or result[:4]!=b'RIFF' or result[8:12]!=b'WAVE':
        raise ValueError('Kokoro no devolvió datos WAV válidos')
    target.write_bytes(result)


def build_ogg(wavs: list[Path], target: Path, folder: Path):
    # Las rutas de WAV son internas al directorio temporal, sin contenido externo.
    playlist=folder/'playlist.txt'
    playlist.write_text(''.join(f"file '{path.name}'\n" for path in wavs),encoding='utf-8')
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                    '-f','concat','-safe','0','-i',str(playlist),
                    '-ac','1','-ar','24000','-c:a','libopus','-b:a','32k',
                    '-vbr','on','-application','voip',str(target)],
                   cwd=folder,check=True,timeout=240)
    if not target.exists() or target.stat().st_size<1024 or target.stat().st_size>45_000_000:
        raise RuntimeError('Salida OGG vacía o demasiado grande para Telegram')


def telegram_send(path: Path, title: str) -> int:
    boundary='----podcast-'+uuid.uuid4().hex
    def fld(name,value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
    content=bytearray()
    content.extend(fld('chat_id',CHAT))
    content.extend(fld('caption',title[:150]))
    content.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="voice"; filename="briefing.ogg"\r\nContent-Type: audio/ogg\r\n\r\n'.encode())
    content.extend(path.read_bytes())
    content.extend(b'\r\n')
    content.extend(f'--{boundary}--\r\n'.encode())
    request=Request(f'https://api.telegram.org/bot{TOKEN}/sendVoice', data=bytes(content),
        headers={'Content-Type':f'multipart/form-data; boundary={boundary}'},method='POST')
    with urlopen(request,timeout=120) as response:
        result=json.load(response)
    if result.get('ok') is not True:
        raise RuntimeError('Telegram no confirmó el envío de voz')
    return int(result['result']['message_id'])


def state_read()->dict:
    if not STATE_FILE.exists():
        return {}
    try:
        obj=json.loads(STATE_FILE.read_text(encoding='utf-8'))
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError):
        raise RuntimeError('Estado de entregas ilegible; detener antes de duplicar audio')


def state_write(content:dict):
    STATE_FILE.parent.mkdir(parents=True,exist_ok=True)
    temp=STATE_FILE.with_name(STATE_FILE.name+'.tmp')
    temp.write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,STATE_FILE)


class Handler(BaseHTTPRequestHandler):
    def send_json(self,status:int,obj:dict):
        payload=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == '/health':
            self.send_json(200,{'ok':True,'service':'podcast-kokoro-bridge'})
        else:
            self.send_json(404,{'ok':False,'error':'not_found'})

    def do_POST(self):
        if self.path != '/render-and-send':
            return self.send_json(404,{'ok':False,'error':'not_found'})
        if not KEY or not hmac.compare_digest(self.headers.get('X-Bridge-Key',''),KEY):
            return self.send_json(401,{'ok':False,'error':'unauthorized'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<2 or length>MAX_REQUEST_BYTES:
                return self.send_json(413,{'ok':False,'error':'request_size_invalid'})
            data=json.loads(self.rfile.read(length).decode('utf-8'))
            script=data.get('script','')
            run_id=str(data.get('run_id',''))
            voice=str(data.get('voice','ef_dora'))
            title=str(data.get('title','Briefing Diario'))
            chat_id=str(data.get('chat_id',''))
            if not isinstance(script,str) or not (500<=len(script)<=MAX_SCRIPT):
                return self.send_json(400,{'ok':False,'error':'invalid_script_length'})
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',run_id):
                return self.send_json(400,{'ok':False,'error':'invalid_run_id'})
            if chat_id != CHAT:
                return self.send_json(403,{'ok':False,'error':'chat_not_allowed'})
            if not re.fullmatch(r'[a-z]{2}_[a-z0-9_]{2,30}',voice):
                return self.send_json(400,{'ok':False,'error':'invalid_voice'})
            with LOCK:
                state=state_read()
                if run_id in state:
                    return self.send_json(200,{'ok':True,'duplicate':True,'message_id':state[run_id]['message_id'],'run_id':run_id})
                parts=split_sentences(script)
                if not parts or len(parts)>100:
                    return self.send_json(400,{'ok':False,'error':'invalid_chunks'})
                with tempfile.TemporaryDirectory(prefix='podcast-kokoro-') as temp:
                    directory=Path(temp)
                    files=[]
                    for index,fragment in enumerate(parts):
                        target=directory/f'{index:04d}.wav'
                        generate_wav(fragment,voice,target)
                        files.append(target)
                    ogg=directory/'briefing.ogg'
                    build_ogg(files,ogg,directory)
                    message_id=telegram_send(ogg,title)
                state[run_id]={'message_id':message_id,'at_utc':datetime.now(timezone.utc).isoformat(),'chunks':len(parts)}
                state_write(dict(sorted(state.items())[-100:]))
                return self.send_json(200,{'ok':True,'duplicate':False,'message_id':message_id,'run_id':run_id,'chunks':len(parts)})
        except (HTTPError,URLError,TimeoutError,subprocess.SubprocessError,RuntimeError,ValueError,OSError) as error:
            self.log_error('Error en TTS/Telegram: %s',type(error).__name__)
            return self.send_json(502,{'ok':False,'error':type(error).__name__,'hint':'Revisa consola de Kokoro, FFmpeg y credenciales'})
        except Exception as error:
            self.log_error('Error inesperado: %s',type(error).__name__)
            return self.send_json(500,{'ok':False,'error':'internal_error'})


if __name__=='__main__':
    if not TOKEN or len(KEY)<24 or not CHAT:
        raise SystemExit('Se requieren TELEGRAM_BOT_TOKEN, ALLOWED_CHAT_ID y BRIDGE_SHARED_KEY >=24 caracteres')
    if shutil.which('ffmpeg') is None:
        raise SystemExit('Falta ffmpeg. Instálalo con brew install ffmpeg')
    print(f'Bridge Kokoro escuchando en {HOST}:{PORT}. Controla el acceso desde LAN con firewall.')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
