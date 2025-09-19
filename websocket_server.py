import asyncio
import websockets
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# ===================================================================
# KONFIGURASI
# ===================================================================
# Memuat environment variables dari file .env
load_dotenv()

# Ambil API key dari environment variable
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY tidak ditemukan. Mohon buat file .env dan tambahkan kunci Anda.")

# Konfigurasi model Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ===================================================================
# LOGIKA INTI SERVER
# ===================================================================
# Set untuk menyimpan semua koneksi klien yang aktif
connected_clients = set()

async def broadcast(message):
    """Mengirim pesan ke semua klien yang terhubung menggunakan asyncio.gather."""
    if connected_clients:
        # Buat daftar tugas (coroutines) untuk mengirim pesan ke setiap klien
        tasks = [client.send(message) for client in connected_clients]
        # Jalankan semua tugas secara bersamaan dan tunggu hingga semuanya selesai
        await asyncio.gather(*tasks)

async def process_conversation(transcript):
    """
    Memproses transkrip ucapan, mendapatkan respons dari LLM.
    """
    print(f"LLM > Menerima transkrip: '{transcript}'")
    
    # Perintahkan klien untuk menampilkan ekspresi 'Berpikir'
    thinking_message = json.dumps({"command": "setExpression", "value": "THINKING"})
    await broadcast(thinking_message)

    try:
        response = await model.generate_content_async(
            f"Anda adalah Asybot, robot asisten yang ramah dan membantu. "
            f"Jawab pertanyaan berikut dengan singkat, jelas, dan dalam Bahasa Indonesia: '{transcript}'"
        )
        
        ai_response_text = response.text.strip()
        print(f"LLM < Menghasilkan respons: '{ai_response_text}'")
        
        return json.dumps({
            "command": "speak",
            "value": ai_response_text
        })
        
    except Exception as e:
        print(f"LLM > Terjadi error saat menghubungi Gemini API: {e}")
        return json.dumps({
            "command": "speak",
            "value": "Maaf, otak saya sedang perlu istirahat sejenak. Coba lagi nanti ya."
        })

async def handler(websocket):
    """
    Menangani koneksi WebSocket yang masuk, satu per klien.
    """
    connected_clients.add(websocket)
    print(f"Server > Klien baru terhubung: {websocket.remote_address}. Total klien: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            print(f"Server < Menerima pesan: {message}")
            try:
                data = json.loads(message)
                
                if data.get("event") == "speechResult":
                    transcript = data.get("transcript", "")
                    
                    if transcript:
                        response_message = await process_conversation(transcript)
                        await websocket.send(response_message)
                        print(f"Server > Mengirim respons ke klien.")
                        
            except json.JSONDecodeError:
                print("Server < Menerima pesan yang bukan JSON.")
            except Exception as e:
                print(f"Server > Terjadi error saat memproses pesan: {e}")

    finally:
        connected_clients.remove(websocket)
        print(f"Server > Klien terputus: {websocket.remote_address}. Total klien: {len(connected_clients)}")

async def main():
    """
    Fungsi utama untuk memulai server WebSocket.
    """
    print("Server > Memulai server WebSocket di ws://localhost:8765...")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer > Server dihentikan oleh pengguna.")

