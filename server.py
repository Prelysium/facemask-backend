## Imports
import urllib.request
import aiohttp_cors
import numpy as np
import aiortc
import json
import sys
import cv2
import os

from mask.detect import inference as detect_masks
from server.ConnectionContainer import ConnectionContainer
from server.ImageGenerator import ImageGenerator
from aiohttp import web
from PIL import Image
from io import BytesIO


# Information for server
ROOT = os.path.dirname(__file__)
routes = web.RouteTableDef()

# Create python classes for container and image storing.
connection_container = ConnectionContainer()
image_generator = ImageGenerator()


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


@routes.get("/")
async def index(request):
    content = open(os.path.join(ROOT, "server/public/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


# This method handels image file requests from the server. 
@routes.get("/api/image")
async def get_file(request):
    # Get request id
    image_id = request.rel_url.query["id"]
    
    # get file 
    image = image_generator.get_image(image_id)
    file_name = image_generator.get_image_name(image_id)
    
    # return file
    return web.Response(
        body=image.getvalue(),
        content_type="image/jpeg",
        headers={"Content-Disposition": 'attachment; filename="' + str(file_name)},
    )

# This endpoint works on file uploading and transformation.
@routes.post("/api/file")
async def file(request):
    post = await request.post()
    # Get all the files
    my_pic_names = []

    for file_name in post:
        file = post.get(file_name)
        img_content = file.file.read()
        # Read image
        pic = BytesIO(img_content)

        ###### Do transformation of image and save it locally.
        image = Image.open(pic).convert("RGB")
        image = np.array(image)
        image = image[:, :, ::-1].copy()
        detect_masks(image, show_result=True)
        Image.fromarray(image).show()

        # saving
        image_id = image_generator.get_image_id()
        with open("server/images/" + str(image_id) + ".png", "wb") as outfile:
            # Copy the BytesIO stream to the output file
            outfile.write(pic.getbuffer())

        # Store the image
        image_generator.add_image(image_id, pic, file_name)
        my_pic_names.append(image_id)

    # return status to the server.
    return web.Response(
        content_type="application/json",
        body=json.dumps({"pic": json.dumps(my_pic_names), "type": "answer"}),
    )


# This endpoint handels video striming offer exchange.
@routes.post("/api/offer")
async def offer(request):
    params = await request.json()
    answer = await connection_container.handle_offer(sdp=params["sdp"], mode="cartoon")

    return web.Response(
        content_type="application/json",
        body=json.dumps({"sdp": answer.sdp, "type": "answer"}),
    )



# Server main
if __name__ == "__main__":
    app = web.Application(client_max_size=100000000)
    app.on_shutdown.append(on_shutdown)

    cors = aiohttp_cors.setup(app)
    resource_offer = cors.add(app.router.add_resource("/api/offer"))
    resource_file = cors.add(app.router.add_resource("/api/file"))
    resource_getfile = cors.add(app.router.add_resource("/api/image"))
    cors.add(
        resource_offer.add_route("POST", offer),
        {
            "http://localhost:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type"),
                max_age=3600,
            )
        },
    )

    cors.add(
        resource_file.add_route("POST", file),
        {
            "http://localhost:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type"),
                max_age=3600,
            )
        },
    )

    cors.add(
        resource_getfile.add_route("GET", get_file),
        {
            "http://localhost:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type"),
                max_age=3600,
            )
        },
    )

    # app.add_routes(routes)
    app.add_routes([web.static("/", ROOT + "server/images")])
    port = 5000 if len(sys.argv) == 1 else sys.argv[1]
    web.run_app(app, port=port)
