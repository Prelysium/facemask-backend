from flask import Flask, url_for, request
import json
from server.ConnectionContainer import ConnectionContainer
import asyncio
from functools import wraps



def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped


app = Flask(__name__)
# Create container
connection_container = ConnectionContainer()


@app.route("/api", methods=["GET"])
def api():
    return {
        'userid': 1,
        'title': 'REZGA',
        'completed': False
    }


async def async_work(data):
    response = await connection_container.handle_offer(sdp=data["sdp"], mode='cartoon')
    return response


@app.route('/api/offer', methods=['POST'])
def postTest():
    print(request.data)
    if not request.json:
        print("ae")
        return "not a json post"

    print("rezga rezga")
    # data = request.get_json(force=True)
    data = request.data
    data = json.loads(data)
    # print("dataL ", data["sdp"])
    answer = asyncio.run(async_work(data))
    # answer = await connection_container.handle_offer(sdp=data["sdp"], mode='cartoon')
    return {'temp': answer.sdp}

# if __name__ == "__main__":
#     app.run()