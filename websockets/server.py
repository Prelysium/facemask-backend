import asyncio
import websockets
import json

connected = set()
async def server(websocket, path):
    # Register.
    connected.add(websocket)
    try:
        async for message in websocket:
            for conn in connected:
                if conn == websocket:
                    await conn.send(json.loads(message))
                    await conn.send(f'Have message for you: {message}')
    finally:
        connected.remove(websocket)


start_server = websockets.serve(server, "localhost", 3000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()