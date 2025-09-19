# Server WebSocket untuk Asybot (Otak Robot)
# Versi 5 - Siap menerima input percakapan, simulator dihapus.

import asyncio
import websockets
import json

CONNECTED_CLIENTS = set()

async def send_command_to_all(command, value):
    if CONNECTED_CLIENTS:
        message = json.dumps({"command": command, "value": value})
        print(f"Server > Mengirim perintah: {message}")
        await asyncio.gather(
            *[client.send(message) for client in CONNECTED_CLIENTS]
        )

async def process_conversation(transcript):
    """
    Placeholder untuk alur kerja AI.
    Di sinilah STT -> LLM -> TTS akan terjadi.
    """
    print(f"Server | AI > Menerima transkrip: '{transcript}'")
    await send_command_to_all("setExpression", "THINKING")
    
    # --- Simulasi Pemrosesan AI ---
    await asyncio.sleep(2)
    response_text = f"Anda mengatakan: {transcript}. Respon dari AI akan ada di sini."
    # --- Akhir Simulasi ---

    print(f"Server | AI > Menghasilkan respons: '{response_text}'")
    await send_command_to_all("speak", response_text)
    await asyncio.sleep(5) # Estimasi waktu bicara
    await send_command_to_all("setExpression", "NEUTRAL")


async def handler(websocket):
    if len(CONNECTED_CLIENTS) >= 1:
        print(f"Server > Menolak koneksi dari {websocket.remote_address}, klien sudah ada.")
        await websocket.close(1013, "Server sibuk")
        return

    CONNECTED_CLIENTS.add(websocket)
    print(f"Server > Klien (Tablet) terhubung dari {websocket.remote_address}")
    
    try:
        # Loop untuk mendengarkan pesan dari klien
        async for message in websocket:
            print(f"Server < Menerima pesan: {message}")
            try:
                data = json.loads(message)
                # Periksa apakah pesan memiliki format yang kita harapkan
                if data.get("event") == "speechResult":
                    transcript = data.get("transcript", "")
                    # Jalankan proses percakapan tanpa memblokir handler
                    asyncio.create_task(process_conversation(transcript))
            except json.JSONDecodeError:
                print("Server < Menerima pesan non-JSON.")
            except Exception as e:
                print(f"Server < Error saat memproses pesan: {e}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Server > Koneksi dari {websocket.remote_address} ditutup.")
    finally:
        if websocket in CONNECTED_CLIENTS:
            CONNECTED_CLIENTS.remove(websocket)
        print(f"Server > Klien dari {websocket.remote_address} dihapus.")


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server > Server WebSocket berjalan di ws://localhost:8765")
        await asyncio.Future()  # Berjalan selamanya

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer > Server dihentikan.")

