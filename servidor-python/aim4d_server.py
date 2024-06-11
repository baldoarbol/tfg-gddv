import socketio
import socket
from aiohttp import web
import base64
import json


async def load_image(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        return encoded_image


sio = socketio.AsyncServer(async_mode='aiohttp')
app = web.Application()
sio.attach(app)
aim4d_instance = None


@sio.event
async def connect(sid, environ):
    aim4d_instance.push_log(f"Client connected: {sid}", [20, 100, 20])


@sio.event
async def disconnect(sid):
    aim4d_instance.push_log(f"Client disconnected: {sid}", [160, 20, 20])


@sio.event
async def message(sid, data):
    aim4d_instance.push_log(f"Message received from {sid}", "black")
    data_dict = None
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON message: {e}")

    reply = create_initial_response()

    for request in data_dict["Requests"]:
        response_header = request["Header"]
        response_output = await aim4d_instance.run_model(request["Header"], request["Prompt"])
        reply = add_response(reply, response_header, response_output)

    await sio.emit('reply', reply, to=sid)
    aim4d_instance.push_log(f"Response sent to {sid}", "black")


async def index(request):
    return web.Response(text="Socket.IO Server", content_type='text/html')

app.router.add_get('/', index)


def create_initial_response():
    initial_data = {"Responses": []}
    return initial_data


def add_response(json_data, header, output):
    new_response = {"Header": header, "Output": output}
    json_data["Responses"].append(new_response)
    return json_data


def create_app():
    global app, sio
    app = web.Application()
    sio.attach(app)

    return app


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(('8.8.8.8', 80))
        ip_local = s.getsockname()[0]
    except Exception as e:
        ip_local = 'No se pudo obtener la IP local: ' + str(e)
    finally:
        s.close()

    return ip_local


runner = None
site = None


async def start_background_server(aim4d):
    global aim4d_instance, runner, site
    aim4d_instance = aim4d
    server = create_app()
    runner = web.AppRunner(server)
    await runner.setup()
    local_ip = get_local_ip()
    server_port = 3000
    site = web.TCPSite(runner, local_ip, server_port)
    await site.start()
    print(f"Server started at http://{local_ip}:{server_port}")
    aim4d_instance.push_log(f"Server started at http://{local_ip}:{server_port}", "yellow")


async def stop_background_server():
    global runner, site
    if site is not None:
        await site.stop()
        print("Site stopped.")
    if runner is not None:
        try:
            await runner.cleanup()
            print("Runner cleaned up.")
        except(RuntimeError) as e:
            print(f"Error while cleaning up: {e}")

    aim4d_instance.push_log(f"Server stopped", "yellow")