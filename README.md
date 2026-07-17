# E2E Encrypted Chatroom Application (Flask-SocketIO & CryptoJS)

This project is a functional Multi-User Chatroom web application designed for a Data Communications class. It features **End-to-End Encryption (E2E)** over WebSockets (TCP) using AES-256 encryption.

---

## 🔒 Encryption & Data Flow (Blind Broadcaster)

The core principle of this project is that the server acts as a **Blind Broadcaster**:

```
[Sender (Key A)] --(Encrypts Plaintext to Ciphertext)--> 
                 [WebSocket: Encrypted Payload] --> 
                                 [Flask Server (Blind Broadcaster)] --> 
                                                 [WebSocket: Encrypted Payload] -->
                                                                 [All Clients]
                                                                       |
      +----------------------------------------------------------------+
      |
      +--> [Client 1 (Key A)] --(Decrypts Ciphertext)--> Success! Plaintext readable.
      |
      +--> [Client 2 (Key B)] --(Decrypts Ciphertext)--> Error! "[Encrypted unreadable message]"
```

1. **Client-side Encryption**: A user inputs their username and a **Shared Secret Key** locally. When a message is sent, the plaintext is encrypted on the client side using the **CryptoJS AES** library before it leaves the browser.
2. **Server-side Routing (Blind Broadcasting)**: The server (`app.py`) receives the encrypted ciphertext payload. It **does not** have access to the Shared Secret Key and cannot decrypt the messages. The server simply broadcasts the ciphertext payload as-is to all other connected clients.
3. **Client-side Decryption**: 
   - Kliens possessing the **same key** will successfully decrypt the message and view it in plaintext.
   - Kliens possessing a **different key** (or no key) will fail to decrypt the ciphertext, resulting in a decryption error. Instead of breaking the UI script, the client catches the error and displays a red `[Encrypted unreadable message]` alert showing the raw ciphertext.

---

## 🛠️ Requirements & Installation

Make sure you have **Python 3.8+** installed.

1. **Clone or copy this folder** to your workspace.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Running the Server Locally

Run the Flask server using Python:

```bash
python app.py
```

The server will start on: **`http://127.0.0.1:5000`**

---

## 🧪 Presentation & Testing Scenarios (Demo Guide)

To demonstrate the End-to-End Encryption (E2E) in a classroom environment:

### Scenario 1: Successful E2E Communication (Same Key)
1. Open **Tab 1** (Browser A) at `http://127.0.0.1:5000`. Enter username **"Ariq"** and Shared Secret Key **"pass123"**.
2. Open **Tab 2** (Browser B) at `http://127.0.0.1:5000`. Enter username **"Raisul"** and Shared Secret Key **"pass123"**.
3. Send a message from Ariq. Raisul's screen will successfully decrypt and display the message.

### Scenario 2: Decryption Failure / Key Mismatch
1. Open **Tab 3** (Browser C) at `http://127.0.0.1:5000`. Enter username **"Alfi"** and Shared Secret Key **"wrong_key_456"**.
2. Send a message from Ariq (from Tab 1).
3. In **Alfi's window**, the message bubble will display:
   - 🔴 **`[Encrypted unreadable message]`**
   - The raw ciphertext block transmitted by the server.
   - A lock badge labeled **"Decryption Error"**.
4. In Ariq and Raisul's windows (who share the same key), their messages are fully readable.

*This proves that the server was completely blind to the plaintext content and only transmitted raw encrypted bytes.*
