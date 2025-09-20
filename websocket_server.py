import asyncio
import websockets
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Muat environment variables dari file .env
load_dotenv()

# ===================================================================
# MODUL LLM (Kecerdasan Buatan)
# ===================================================================
class AsybotLLM:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Error: GOOGLE_API_KEY tidak ditemukan di file .env")
        
        genai.configure(api_key=self.api_key)
        
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        self.system_instruction = "Kamu adalah Asybot, robot asisten yang ramah dan ekspresif. Selalu jawab dalam Bahasa Indonesia. PENTING: Jawabanmu HARUS dalam format JSON. Formatnya adalah: {\"expression\": \"jenis_ekspresi\", \"response\": \"teks_jawabanmu\"}. 'jenis_ekspresi' bisa berupa 'netral', 'senang', 'terkejut', atau 'berpikir'. Contoh: {\"expression\": \"senang\", \"response\": \"Tentu, saya senang bisa membantu!\"}"
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            safety_settings=self.safety_settings,
            generation_config=self.generation_config,
            system_instruction=self.system_instruction
        )

    async def get_response(self, transcript):
        print(f"LLM > Menerima transkrip: '{transcript}'")
        try:
            chat_session = self.model.start_chat(history=[])
            response = await chat_session.send_message_async(transcript)
            # Mengembalikan respons JSON mentah dari AI
            return response.text
        except Exception as e:
            print(f"LLM Error: {e}")
            error_response = {"expression": "netral", "response": "Maaf, terjadi sedikit gangguan di sirkuit berpikir saya."}
            return json.dumps(error_response)

# Inisialisasi LLM
llm = AsybotLLM()
# Kumpulan klien yang terhubung
connected_clients = set()

async def broadcast(message):
    if connected_clients:
        # Menggunakan asyncio.gather untuk mengirim pesan ke semua klien secara bersamaan
        await asyncio.gather(
            *[client.send(message) for client in connected_clients]
        )

async def process_conversation(transcript):
    """Memproses transkrip dan mendapatkan respons dari LLM."""
    response_json = await llm.get_response(transcript)
    return response_json

async def handler(websocket):
    """Menangani koneksi WebSocket yang masuk."""
    # Daftarkan klien baru
    connected_clients.add(websocket)
    print(f"Server > Klien baru terhubung: {websocket.remote_address}. Total klien: {len(connected_clients)}")
    
    try:
        # Loop untuk mendengarkan pesan dari klien
        async for message in websocket:
            print(f"Server < Menerima pesan: {message[:100]}...") # Log pesan yang masuk
            try:
                data = json.loads(message)
                if data.get("event") == "speechResult":
                    transcript = data.get("transcript", "")
                    if transcript:
                        # Proses ucapan dan dapatkan respons AI
                        response_message = await process_conversation(transcript)
                        
                        # Kirimkan respons kembali ke semua klien
                        print(f"Server > Mengirim respons: {response_message}")
                        await broadcast(response_message)

            except json.JSONDecodeError:
                print("Server > Menerima pesan yang bukan JSON.")
            except Exception as e:
                print(f"Server > Terjadi error saat memproses pesan: {e}")

    finally:
        # Hapus klien saat koneksi terputus
        connected_clients.remove(websocket)
        print(f"Server > Klien terputus: {websocket.remote_address}. Total klien: {len(connected_clients)}")

async def main():
    print("Server > Memulai server WebSocket di ws://localhost:8765...")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # Jalankan selamanya

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer > Server dihentikan.")

