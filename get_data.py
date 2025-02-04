import json
import asyncio
from dataclasses import dataclass
from requests_api_go import fkapi_get_op_data_by_codigo

@dataclass
class OrdemProducao:
    number: int
    code: str
    client: str
    description: str
    barcode: str
    quantity: str
    box_count: int
    weight: float

    def __init__(self, number: int, code: str, client: str, description: str, barcode: str, quantity: str, box_count: int = "1", weight: float = ""):
        self.number = number
        self.code = code
        self.client = client
        self.description = description
        self.barcode = barcode
        self.quantity = quantity
        self.box_count = box_count
        self.weight = weight

async def get_data_by_codigo(codigo_ordem_producao: str) -> OrdemProducao | None:
    try:
        op_data: dict = await fkapi_get_op_data_by_codigo(codigo_ordem_producao)
        if op_data is None:
            print(op_data)
            return None
        op_data = json.loads(op_data)
        return OrdemProducao(
            number=op_data["codigoOrdemProducao"],
            code=op_data["codigoMaterial"],
            client=op_data["cliente"],
            description=op_data["descricaoMaterial"],
            barcode=op_data["descricaoMaterial"],
            quantity=op_data["quantidade"]
        )

    except json.decoder.JSONDecodeError:
        return "Erro ao decodificar JSON"
    except Exception as e:
        return f"Erro: {e}"
    


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data_by_codigo("223536"))