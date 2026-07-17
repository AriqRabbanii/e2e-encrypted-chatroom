import os
import sys
import time
import base64
import hashlib
import threading
import socketio
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ANSI Escape Codes for Premium UI Aesthetics
CLEAR_LINE = "\r\033[K"
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_GRAY = "\033[90m"
COLOR_MAGENTA = "\033[95m"
COLOR_BG_RED = "\033[41m\033[37m"

# Global states
sio = socketio.Client()
username = ""
encryption_key = ""
prompt_active = False

def evp_bytestokey(password: bytes, salt: bytes, key_len=32, iv_len=16) -> tuple[bytes, bytes]:
    """Derive key and IV using OpenSSL-compatible EvpKDF (compatible with CryptoJS)."""
    derived = b''
    last = b''
    while len(derived) < (key_len + iv_len):
        last = hashlib.md5(last + password + salt).digest()
        derived += last
    return derived[:key_len], derived[key_len:key_len+iv_len]

def decrypt_cryptojs(ciphertext_b64: str, password: str) -> str:
    """Decrypt ciphertext encrypted with CryptoJS.AES.encrypt."""
    data = base64.b64decode(ciphertext_b64)
    if not data.startswith(b'Salted__'):
        raise ValueError("Invalid CryptoJS ciphertext (missing Salted__ prefix)")
    salt = data[8:16]
    ciphertext = data[16:]
    key, iv = evp_bytestokey(password.encode('utf-8'), salt, 32, 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return decrypted.decode('utf-8')

def encrypt_cryptojs(plaintext: str, password: str) -> str:
    """Encrypt plaintext compatible with CryptoJS.AES.encrypt."""
    salt = os.urandom(8)
    key, iv = evp_bytestokey(password.encode('utf-8'), salt, 32, 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    payload = b'Salted__' + salt + ciphertext
    return base64.b64encode(payload).decode('utf-8')

def safe_print(text: str):
    """Print message to console safely without disrupting the input prompt."""
    if prompt_active:
        sys.stdout.write(f"{CLEAR_LINE}{text}\nPesan: ")
        sys.stdout.flush()
    else:
        print(text)

@sio.event
def connect():
    safe_print(f"{COLOR_GREEN}[✔] Terhubung ke server WebSocket!{COLOR_RESET}")
    # Emit join event
    sio.emit('join', {'username': username})

@sio.event
def disconnect():
    safe_print(f"{COLOR_RED}[✖] Terputus dari server WebSocket.{COLOR_RESET}")

@sio.on('system_message')
def on_system_message(data):
    msg = data.get('message', '')
    safe_print(f"{COLOR_GRAY}[SISTEM] {msg}{COLOR_RESET}")

@sio.on('receive_message')
def on_receive_message(data):
    sender = data.get('username')
    ciphertext = data.get('ciphertext')
    timestamp = data.get('timestamp')
    
    # Do not print self messages to avoid duplicate prompt disruption
    if sender == username:
        return
        
    try:
        decrypted = decrypt_cryptojs(ciphertext, encryption_key)
        # Display successful decryption with secure padlock icon
        safe_print(
            f"{COLOR_CYAN}[{timestamp}] {COLOR_GREEN}🔓 {sender}:{COLOR_RESET} {decrypted}"
        )
    except Exception:
        # Display red decryption error block
        error_msg = (
            f"\n{COLOR_BG_RED} 🔴 [DECRYPTION ERROR] Gagal mendekripsi pesan dari '{sender}' {COLOR_RESET}\n"
            f"{COLOR_GRAY}   Raw Ciphertext: {ciphertext}\n"
            f"   Kunci Anda tidak cocok atau pesan terdistorsi.{COLOR_RESET}"
        )
        safe_print(error_msg)

def print_banner():
    # Clear console for premium feel
    os.system('clear' if os.name == 'posix' else 'cls')
    
    banner = f"""
{COLOR_CYAN}=============================================================
             🛡️  E2E ENCRYPTED CHATROOM CLI CLIENT  🛡️
         (Compatible with CryptoJS & Flask-SocketIO)
============================================================={COLOR_RESET}
    """
    print(banner)

def main():
    global username, encryption_key, prompt_active
    print_banner()
    
    # Server configuration
    server_url = input(f"Masukkan URL Server [{COLOR_GREEN}http://127.0.0.1:5000{COLOR_RESET}]: ").strip()
    if not server_url:
        server_url = "http://127.0.0.1:5000"
        
    # Username configuration
    username = input(f"Masukkan Username (cth: Ariq, Raisul, Alfi): ").strip()
    while not username:
        username = input(f"Username tidak boleh kosong. Masukkan Username: ").strip()
        
    # Shared Key configuration
    encryption_key = input(f"Masukkan Kunci Enkripsi (Shared Key): ").strip()
    while not encryption_key:
        encryption_key = input(f"Kunci tidak boleh kosong. Masukkan Kunci: ").strip()
        
    print(f"\n{COLOR_YELLOW}[*] Menghubungkan ke {server_url}...{COLOR_RESET}")
    
    try:
        sio.connect(server_url)
    except Exception as e:
        print(f"{COLOR_RED}[!] Gagal terhubung ke server: {e}{COLOR_RESET}")
        return

    # Give a brief moment to join and print system updates
    time.sleep(0.5)
    
    print(f"\n{COLOR_GREEN}[✔] Masuk sebagai: {username}{COLOR_RESET}")
    print(f"{COLOR_GREEN}[✔] Kunci Enkripsi Aktif: {encryption_key}{COLOR_RESET}")
    print(f"{COLOR_GRAY}[*] Ketik pesan Anda dan tekan Enter. Ketik '/exit' untuk keluar.{COLOR_RESET}\n")
    
    prompt_active = True
    try:
        while True:
            # We use custom prompt_active to prevent print overlap issues
            msg = input("Pesan: ").strip()
            if not msg:
                continue
            
            if msg.lower() in ['/exit', '/quit']:
                break
                
            if msg.lower() == '/info':
                prompt_active = False
                safe_print(f"{COLOR_CYAN}--- Info Status ---")
                safe_print(f"User: {username}")
                safe_print(f"Key: {encryption_key}")
                safe_print(f"Server: {server_url}{COLOR_RESET}")
                prompt_active = True
                continue
                
            # Encrypt locally
            try:
                ciphertext = encrypt_cryptojs(msg, encryption_key)
                timestamp = datetime.now().strftime("%H:%M")
                
                # Emit to server
                sio.emit('send_message', {
                    'username': username,
                    'ciphertext': ciphertext,
                    'timestamp': timestamp
                })
                
                # Print self message instantly on CLI so user sees their own message
                prompt_active = False
                safe_print(f"{COLOR_CYAN}[{timestamp}] {COLOR_MAGENTA}🔒 {username} (Anda):{COLOR_RESET} {msg}")
                prompt_active = True
                
            except Exception as e:
                prompt_active = False
                safe_print(f"{COLOR_RED}[!] Gagal mengenkripsi/mengirim pesan: {e}{COLOR_RESET}")
                prompt_active = True
                
    except KeyboardInterrupt:
        pass
    finally:
        prompt_active = False
        print(f"\n{COLOR_YELLOW}[*] Keluar dari chatroom dan memutuskan koneksi...{COLOR_RESET}")
        sio.disconnect()
        print(f"{COLOR_GREEN}[✔] Selesai!{COLOR_RESET}")

if __name__ == '__main__':
    main()
