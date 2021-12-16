import base64
import pickle


async def generator_streamer(data):
    yield base64.b64encode(pickle.dumps(data))
