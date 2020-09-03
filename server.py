import asyncio
import websockets
import json
from server.ConnectionContainer import ConnectionContainer
import sys
from PIL import Image
from io import BytesIO

# Create container
connection_container = ConnectionContainer()


# WebSocket server
async def server(websocket, path):
    # Take request parse and send message back.
    async for message in websocket:
        print(message)
        if isinstance(message, bytes):
            stream = BytesIO(message)
            image = Image.open(stream).convert("RGBA")
            stream.close()
            image.show()
        else:
            params = json.loads(message)
            # Taking video streaming sdp
            answer = await connection_container.handle_offer(
                sdp=params["sdp"], mode="cartoon"
            )
            await websocket.send(answer.sdp)


# Start websocket server
start_server = websockets.serve(server, "localhost", 5000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
