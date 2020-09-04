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
from mask.utils import write_output_video
from server.ConnectionContainer import ConnectionContainer
from server.ImageGenerator import ImageGenerator
from server.OpenCVStreamTrack import message_class
message_class
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
        if file.content_type.split('/')[0] == 'video':
            video_path = './server/videos/{}'.format(file.filename)
            video_content = file.file.read()
            video = BytesIO(video_content)
            # save video
            with open(video_path, "wb") as outfile:
                outfile.write(video.getbuffer())
            outfile.close()

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Video open failed.")
                return

            writer = write_output_video(cap, './server/videos/output/' + file.filename.split('.')[0] + '.avi')
            status_video_capture = True
            while status_video_capture:
                status_video_capture, img_raw = cap.read()
                if status_video_capture:
                    img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
                    detect_masks(img_raw)
                    img_raw = cv2.cvtColor(img_raw, cv2.COLOR_RGB2BGR)
                    writer.write(img_raw[:, :, :])

            # Store the video
            my_pic_names.append(file.filename.split('.')[0] + '.avi')
            # os.remove(video_path)
        else:
            img_content = file.file.read()
            # Read image
            pic = BytesIO(img_content)

            ###### Do transformation of image and save it locally.
            image = Image.open(pic).convert("RGB")
            image = np.array(image)
            image = image[:, :, ::-1].copy()
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            detect_masks(image, show_result=True)
            image = Image.fromarray(image)

            # saving
            image_id = image_generator.get_image_id()
            with open("server/images/" + str(image_id) + ".jpeg", "wb") as outfile:
                # Copy the BytesIO stream to the output file
                outfile.write(pic.getbuffer())

            imgByteArr = BytesIO()
            image.save(imgByteArr, format="JPEG")
            # Store the image
            image_generator.add_image(
                image_id, imgByteArr, file_name.split(".")[0] + ".jpeg"
            )
            my_pic_names.append(image_id)
            os.remove('./server/images/' + str(image_id) + '.jpeg')

    # return status to the server.
    return web.Response(
        content_type="application/json",
        body=json.dumps({"pic": json.dumps(my_pic_names), "type": "answer"}),
    )


# This endpoint handles video streaming offer exchange.
@routes.post("/api/offer")
async def offer(request):
    params = await request.json()
    mode_on = params["mode"]
    answer = await connection_container.handle_offer(sdp=params["sdp"], mode=mode_on)

    return web.Response(
        content_type="application/json",
        body=json.dumps({"sdp": answer.sdp, "type": "answer"}),
    )

@routes.get("/api/status")
async def status(request):
    num = message_class.get()

    return web.Response(
        content_type="application/json",
        body=json.dumps({"number": num}),
    )


# Server main
if __name__ == "__main__":
    app = web.Application(client_max_size=100000000)
    app.on_shutdown.append(on_shutdown)

    cors = aiohttp_cors.setup(app)
    resource_offer = cors.add(app.router.add_resource("/api/offer"))
    resource_status = cors.add(app.router.add_resource("/api/status"))
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
        resource_status.add_route("GET", status),
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
    app.add_routes([web.static("/", ROOT + "server")])
    port = 5000 if len(sys.argv) == 1 else sys.argv[1]
    web.run_app(app, port=port)
