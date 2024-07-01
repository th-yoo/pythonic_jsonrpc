from typing import TypeVar, Generic, Union
import asyncio
import json
from pydantic import ValidationError
from .pkt import JsonRpcRequest, JsonRpcError, JsonRpcResponse, JsonRpcBatchResponse

class JsonRpcInvalidParamError(Exception):
    pass

T = TypeVar('T')

class jsonrpc_t(Generic[T]):
    def __init__(self, methods: T):
        # TODO
        self.methods = methods

#    async def request(self, req):
#        if isinstance(req, str):
#            return await self.request_str(req)
#        return await self.request_obj(req)
#
#    async def request_obj(self, req: Union[dict,list]):
#            if isinstance(req, dict):
#                return await self.call(req)
#            elif isinstance(req, list):
#                return await self.batch_call(req)
#            return JsonRpcResponse(
#                error = JsonRpcError(
#                    code = -32700,
#                    message = 'Parse Error'
#                )
#            )

    async def request(self, req_pkt: str):
        try:
            req = json.loads(req_pkt)

            resp = None
            if not isinstance(req, list):
                resp = await self.call(req)
            else:
                resp = await self.batch_call(req)
            return resp
        except json.JSONDecodeError:
            return JsonRpcResponse(
                error = JsonRpcError(
                    code = -32700,
                    message = 'Parse error'
                )
            )
        except Exception as e:
            print(e)

    async def call(self, raw_req: dict):
        try:
            req = JsonRpcRequest.model_validate(raw_req)
        except ValidationError as e:
            return JsonRpcResponse(
                error = JsonRpcError(
                    code = -32600,
                    message = 'Invalid Request'
                )
            )
        except Exception as e:
            print(e)

        try:
            method = self.get_method(req.method)
            if not method:
                return JsonRpcResponse(
                    id=req.id,
                    error = JsonRpcError(
                        code = -32601,
                        message = 'Method not found'
                    )
                )
        except Exception as e:
            print(e)

        try:
            result = await self.call_method(method, req.params)
        except JsonRpcInvalidParamError as e:
            return JsonRpcResponse(
                id=req.id,
                error=JsonRpcError(
                    code=-32602,
                    message='Invalid params'
                )
            )
        except Exception as e:
            return JsonRpcResponse(
                id=req.id,
                error=JsonRpcError(
                    code=-32603,
                    message='Internal error',
                    data=str(e)
                )
            )

        if not req.id:
            return
        return JsonRpcResponse(id=req.id, result=result)


    async def batch_call(self, reqs: list):
        if not len(reqs):
            # FIXME: code duplication
            return JsonRpcResponse(
                error=JsonRpcError(
                    code=-32600,
                    message='Invalid Request'
                )
            )

        corutines = [self.call(req) for req in reqs]
        rv = list(filter(None, await asyncio.gather(*corutines)))

        # notifications
        if not len(rv):
            return
        return JsonRpcBatchResponse(rv)


    def get_method(self, method: str):

        rv = getattr(self.methods, method, None)
        if callable(rv):
            return rv

    async def call_method(self, method, params):
        if not params:
            result = await method()
        elif isinstance(params, list):
            result = await method(*params)
        elif isinstance(params, dict):
            result = await method(**params)
        else:
            result = await method(params)
        return result
   


if __name__ == '__main__':
    j = jsonrpc_t(0)
