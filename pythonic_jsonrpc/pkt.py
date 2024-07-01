#from typing import List, Optional, Any, Union, Literal, Type, ClassVar
from typing import List, Optional, Any, Union, Literal
from pydantic import BaseModel, RootModel

# TODO: replace pydantic with zon (zod porting)
# Sigh: zon depends on python 3.11 and above (Isn't it overspec?)
from dataclasses import dataclass, asdict
import json

JSONRPC_VER = '2.0'

class JsonRpcRequest(BaseModel):
    jsonrpc: Literal[JSONRPC_VER] = JSONRPC_VER
    method: str
    params: Optional[Union[List[Any], dict]] = None
    id: Optional[Union[int, str]] = None

class JsonRpcResponseSerializer(json.JSONEncoder):
    def default(self, o):
        def trim_error(rv):
            if rv['data'] is None:
                del rv['data']
            return rv

        def trim_resp(rv): 
            if rv['error'] is None:
                assert rv['id'] is not None, 'id is missing'
                del rv['error']
            else:
                assert rv['result'] is None, 'Both of result and error exist'
                del rv['result']
                trim_error(rv['error'])
            return rv

        if isinstance(o, JsonRpcResponse):
            return trim_resp(asdict(o))
        elif isinstance(o, JsonRpcError):
            return trim_error(asdict(o))
        return super().default(o)


class Packetizer:
    #_packetizer: ClassVar[Type[json.JSONEncoder]] = JsonRpcErrorSerializer

    def packetize(self) -> str:
        #return json.dumps(self, cls=getattr(type(self), '_packetizer'))
        return json.dumps(
            self,
            cls=JsonRpcResponseSerializer,
            ensure_ascii=False,
        )


@dataclass
class JsonRpcError(Packetizer):
   code: int = -32603
   message: str = 'Internal error'
   data: Optional[Any] = None

# with pydantic, it's too verbose to validate one of result & error field should exist exclusively.
@dataclass
class JsonRpcResponse(Packetizer):
    jsonrpc: Literal[JSONRPC_VER] = JSONRPC_VER
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None
    id: Optional[Union[int, str, None]] = None

class JsonRpcBatchResponse(list, Packetizer):
    pass

if __name__ == '__main__':
    e = JsonRpcError()
    #print(json.dumps(e, indent=4, cls=e._packetizer))
    print(e.packetize())

    resp0 = JsonRpcResponse(id=0)
    #print(resp.packetize())

    resp = JsonRpcResponse(result=1, id=1)
    print(resp.packetize())

    #resp2 = JsonRpcResponse(result=1, error=e)
    #print(resp2.packetize())

    resp1 = JsonRpcResponse(id='01')
    print(resp1.packetize())

    resp3 = JsonRpcResponse(error=e)
    print(resp3.packetize())

    resp3_ = JsonRpcResponse(error=e, id=3)
    print(resp3_.packetize())

    resp4 = JsonRpcBatchResponse([resp, resp3])
    print(resp4.packetize())

