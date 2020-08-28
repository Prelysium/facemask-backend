import asyncio
import os
import json
from aiohttp import web
import sys

from server.ConnectionContainer import ConnectionContainer


ROOT = os.path.dirname(__file__)
routes = web.RouteTableDef()

connection_container = ConnectionContainer()

import aiortc

def aiortc_multiple_stream_patch() -> None:
    def _patched_route_rtp(self, packet):
        ssrc_receiver = self.ssrc_table.get(packet.ssrc)

        # the SSRC are known
        if ssrc_receiver is not None:
            return ssrc_receiver

        pt_receiver = self.payload_type_table.get(packet.payload_type)

        # the SSRC is unknown but the payload type matches, update the SSRC table
        if ssrc_receiver is None and pt_receiver is not None:
            self.ssrc_table[packet.ssrc] = pt_receiver
            return pt_receiver

        # discard the packet
        return None

    aiortc.rtcdtlstransport.RtpRouter.route_rtp = _patched_route_rtp

aiortc_multiple_stream_patch()


async def on_shutdown():
    pass


@routes.get('/')
async def index(request):
    content = open(os.path.join(ROOT, "server/public/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


@routes.post('/offer')
async def offer(request):
    params = await request.json()

    answer = await connection_container.handle_offer(sdp=params["sdp"], mode=params["mode"])
    print(params["mode"])

    return web.Response(content_type='application/json',
                        body=json.dumps({"sdp": answer.sdp, "type": "answer"})
                        )

if __name__ == '__main__':
    app = web.Application()
    app.on_shutdown.append(on_shutdown)

    app.add_routes(routes)
    app.add_routes([web.static('/', ROOT + 'server/public')])
    port = 3000 if len(sys.argv) == 1 else sys.argv[1]
    web.run_app(app, port=port)
