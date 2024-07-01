# https://github.com/python-poetry/poetry/issues/34#issuecomment-1193365526
# $ poetry install      # editible (dev mode)

import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request, Response
from fastapi import WebSocket, WebSocketDisconnect

from pythonic_jsonrpc import jsonrpc_t, JsonRpcInvalidParamError

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'))

class RpcTestMethods:
    async def subtract(self, *args, **kwargs):
        # we don't test data types of args
        lhs = 0
        rhs = 0
        print('subtract', args, kwargs)
        if args:
            if len(args) != 2 or kwargs:
                raise JsonRpcInvalidParamError()
            lhs, rhs = args
        elif kwargs:
            if all(hasattr(kwargs, arg) for arg in ('minuend', 'subtrahend')):
                raise JsonRpcInvalidParamError()
            lhs = kwargs['minuend']
            rhs = kwargs['subtrahend']
        else:
            raise JsonRpcInvalidParamError()

        return lhs - rhs

    async def sum(self, *args):
        return sum(args)

    async def get_data(self):
        return ['hello', 5]

    #
    # notification
    #
    async def update(self, *args):
        print('update', args)

    async def notify_hello(self, *args, **kwargs):
        print('notify_hello', args, kwargs)

    async def notify_sum(self, *args):
        print('notify_sum', args)

jsonrpc = jsonrpc_t(RpcTestMethods())

@app.get('/')
async def read_index():
    return FileResponse('static/client.html')

# fastapi over-automated
@app.post('/api')
async def http_jsonrpc_endpoint(req: Request):
    if not req.headers.get('Content-Type').startswith('application/json'):
        raise HTTPException(
            status_code = 415,
            detail="Unsupported Media Type. Expected 'application/json'."
        )
    body = await req.body()
    if isinstance(body, bytes):
        body = body.decode('utf-8')

    resp = await jsonrpc.request(body)

    # notification
    if not resp: return

    # over-automated again
    return Response(
        content=resp.packetize(),
        media_type='application/json'
    )

@app.websocket('/api')
async def ws_jsonrpc_endpoint(websocket: WebSocket):
    await websocket.accept()
    print('accepted')
    try:
        while True:
            req = await websocket.receive_text()
            print(req)
            resp = await jsonrpc.request(req)
            if not resp: continue
            print(resp)
            await websocket.send_text(resp.packetize())

    except WebSocketDisconnect as e:
        print(e)
    except Exception as e:
        print(e)

