import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from requests_api_go import fkapi_get_op_data_by_codigo

@dataclass
class OrdemDeProducao:
    code: int
    code_material: str
    client: str
    description: str
    barcode: str
    quantity: str
    box_count: int
    weight: float

    def __init__(self, code: int, code_material: str, client: str, description: str, barcode: str, quantity: str, box_count: int = "1", weight: float = ""):
        self.code = code
        self.code_material = code_material
        self.client = client
        self.description = description
        self.barcode = barcode
        self.quantity = quantity
        self.box_count = box_count
        self.weight = weight

class OrdensDeProducao:
    # Atributo de classe para armazenar a lista de dicionários
    instances: dict[int, int] = {}

    @classmethod
    def create(cls, code: int, code_material: str, client: str, description: str, barcode: str, quantity: int) -> None:
        # Cria uma nova instância de OP
        instance = OrdemDeProducao(code, code_material, client, description, barcode, code_material, quantity)
        cls.instances[instance.code] = asdict(instance)

    @classmethod
    def get_instances(cls) -> "OrdensDeProducao":
        return cls.instances

    @classmethod
    def find_by_codigo(cls, code) -> dict[int, int]:
        return cls.instances.get(code, None)

def format_carga_maquina_json_data_to_op(raw: str):
    # Convertendo get do scraping para html
        soup = BeautifulSoup(raw, 'html.parser')

        # Pegando todos table rows da tabela a partir do 1°
        trs = soup.find_all('tr')[1:]

        # Iterando a pagina para coleta dos dados das Ordens de Produção e passando para uma classe
        for tr in trs:
          code: int = int(tr.find_all("td")[2].get_text(separator='', strip=True).split('-')[-1])
          codigo_material: str = tr.find_all("td")[4].get_text(separator='', strip=True)
          client: str = tr.find_all("td")[3].get_text(separator='', strip=True)
          description: str = tr.find_all("td")[5].get_text(separator='', strip=True)
          quantity: int = int(tr.find_all("td")[6].get_text(separator='', strip=True))

          OrdensDeProducao.create(code, codigo_material, client, description, description, quantity)

        # Formatando as ordens de produção para formato JSON decofidicado para UTF-8
        json_string: str = json.dumps(OrdensDeProducao.get_instances(), indent=2, ensure_ascii=False)
        json_string.encode("utf-8")

        print(json_string)

async def get_op_data_by_codigo(codigo_ordem_producao: str) -> OrdemDeProducao | None:
    try:
        op_data: dict = await fkapi_get_op_data_by_codigo(codigo_ordem_producao)
        if op_data is None:
            print(op_data)
            return None
        op_data = json.loads(op_data)
        return OrdemDeProducao(
            code=op_data["codigoOrdemProducao"],
            code_material=op_data["codigoMaterial"],
            client=op_data["cliente"],
            description=op_data["descricaoMaterial"],
            barcode=op_data["descricaoMaterial"],
            quantity=op_data["quantidade"]
        )

    except json.decoder.JSONDecodeError:
        return "Erro ao decodificar JSON"
    except Exception as e:
        return f"Erro: {e}"

async def get_all_op_data_on_carga_maquina():
    login_url: str = 'https://app.cargamaquina.com.br/site/login?c=31.1%7E78%2C8%5E56%2C8'

    login_payload: dict[str,str] = {
        "LoginForm[username]": "",
        "LoginForm[password]": "",
        "LoginForm[codigoConexao]": "31.1~78,8^56,8",
        "yt0": "Entrar"
      }


    url: str = 'https://app.cargamaquina.com.br/ordemProducao/exportarOrdens'
    params: dict[str,str] = {
        'OrdemProducao[codigo]': '',
        'OrdemProducao[_nomeCliente]': '',
        'OrdemProducao[_nomeMaterial]': '',
        'OrdemProducao[status_op_id]': 'Todos',
        'OrdemProducao[_etapasPlanejadas]': '',
        'OrdemProducao[forecast]': '0',
        'OrdemProducao[_inicioCriacao]': '',
        'OrdemProducao[_fimCriacao]': '',
        'OrdemProducao[_inicioEntrega]': '01/01/2025',
        'OrdemProducao[_fimEntrega]': '15/01/2025',
        'OrdemProducao[_limparFiltro]': '0',
        'pageSize': '20',
    }
    print("Trying to login with aiohttp")
    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, data=login_payload) as response:
            if not response.ok:
                print("Login failed")
            if response.ok:
                print("Login successful")
                async with session.get(url, params=params) as response:
                    if not response.ok:
                        return {}
                    if response.ok:
                        data = await response.text()
                        print("Get data sucessful, trying to convert to json")
                        format_carga_maquina_json_data_to_op(data)

def test_fkapi_get():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_op_data_by_codigo("223536"))

def test_carga_maquina_get():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_op_data_on_carga_maquina())

if __name__ == "__main__":
    test_carga_maquina_get()