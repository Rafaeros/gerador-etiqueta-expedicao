import re
import json
import pathlib
import asyncio
import aiohttp
from datetime import timedelta, datetime as dt
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from core.requests_api_go import fkapi_get_op_data_by_codigo

TMP_PATH = "./tmp/"


@dataclass
class OrdemDeProducao:
    code: int
    material_code: str
    client: str
    client_code: str
    description: str
    barcode: str
    quantity: str
    box_count: int
    weight: int | str

    def __init__(
        self,
        code: int,
        material_code: str,
        client: str,
        description: str,
        barcode: str,
        quantity: int,
        box_count: int = "1",
        weight: int = 0,
    ):
        self.code = code
        self.material_code = material_code
        self.client = client
        self.client_code = ""
        self.description = description
        self.barcode = barcode
        self.quantity = quantity
        self.box_count = box_count
        self.weight = weight
        self.get_client_code()
        self.update_barcode()

    def get_client_code(self) -> None:
        regex = r"\((.*?)\)"
        code = re.search(regex, self.description)
        if code is None:
            self.client_code = ""
            return
        self.client_code = code.group(1)
        return

    def update_barcode(
        self,
    ) -> None:
        if self.client_code == "":
            return
        self.barcode = f"{self.material_code} ({self.client_code})"


class OrdensDeProducao:
    # Atributo de classe para armazenar a lista de dicionários
    instances: dict[int, int] = {}

    @classmethod
    def create(
        cls,
        code: int,
        material_code: str,
        client: str,
        description: str,
        barcode: str,
        quantity: int,
        box_count: int,
        weight: int,
    ) -> None:
        # Cria uma nova instância de OP
        instance = OrdemDeProducao(
            code,
            material_code,
            client,
            description,
            barcode,
            quantity,
            box_count,
            weight,
        )
        instance.get_client_code()
        instance.update_barcode()
        cls.instances[instance.code] = asdict(instance)

    @classmethod
    def get_instances(cls) -> "OrdensDeProducao":
        return cls.instances

    @classmethod
    def find_by_codigo(cls, code) -> dict[int, int]:
        return cls.instances.get(code, None)


def format_carga_maquina_json_data_to_op(
    raw: str, start_deliver_date: str, end_deliver_date: str
) -> str | None:
    soup = BeautifulSoup(raw, "html.parser")
    trs = soup.find_all("tr")[1:]
    for tr in trs:
        code: int = int(
            tr.find_all("td")[2].get_text(separator="", strip=True).split("-")[-1][1:7]
        )
        material_code: str = tr.find_all("td")[4].get_text(separator="", strip=True)
        client: str = tr.find_all("td")[3].get_text(separator="", strip=True)
        description: str = tr.find_all("td")[5].get_text(separator="", strip=True)
        quantity: int = int(tr.find_all("td")[6].get_text(separator="", strip=True))
        OrdensDeProducao.create(
            code, material_code, client, description, material_code, quantity, 1, 0
        )

    json_string = json.dumps(
        OrdensDeProducao.get_instances(), indent=4, ensure_ascii=False
    )
    json_string.encode("utf-8")

    if not pathlib.Path(TMP_PATH).exists():
        pathlib.Path(TMP_PATH).mkdir()

    start_deliver_date = start_deliver_date.replace("/", "-")
    end_deliver_date = end_deliver_date.replace("/", "-")

    with open(
        f"{TMP_PATH}ordens_{start_deliver_date}_{end_deliver_date}.json", "w"
    ) as file:
        json.dump(OrdensDeProducao.get_instances(), file, indent=4, ensure_ascii=False)
        return json_string
    return None


async def get_op_data_by_codigo(codigo_ordem_producao: str) -> OrdemDeProducao | None:
    try:
        op_data: dict = await fkapi_get_op_data_by_codigo(codigo_ordem_producao)
        if op_data is None:
            return None
        op_data = json.loads(op_data)
        return OrdemDeProducao(
            code=op_data["codigoOrdemProducao"],
            material_code=op_data["codigoMaterial"],
            client=op_data["cliente"],
            description=op_data["descricaoMaterial"],
            barcode=op_data["descricaoMaterial"],
            quantity=op_data["quantidade"],
        )
    except json.decoder.JSONDecodeError:
        return None
    except Exception as e:
        return None


async def get_all_op_data_on_carga_maquina() -> dict | None:
    login_url: str = (
        "https://app.cargamaquina.com.br/site/login?c=31.1%7E78%2C8%5E56%2C8"
    )

    login_payload: dict[str, str] = {
        "LoginForm[username]": "",
        "LoginForm[password]": "",
        "LoginForm[codigoConexao]": "31.1~78,8^56,8",
        "yt0": "Entrar",
    }

    start_deliver_date: str = (dt.now() - timedelta(days=35)).strftime("%d/%m/%Y")
    end_deliver_date: str = (dt.now() + timedelta(days=35)).strftime("%d/%m/%Y")
    url: str = "https://app.cargamaquina.com.br/ordemProducao/exportarOrdens"
    params: dict[str, str] = {
        "OrdemProducao[codigo]": "",
        "OrdemProducao[_nomeCliente]": "",
        "OrdemProducao[_nomeMaterial]": "",
        "OrdemProducao[status_op_id]": "Todos",
        "OrdemProducao[_etapasPlanejadas]": "",
        "OrdemProducao[forecast]": "0",
        "OrdemProducao[_inicioCriacao]": "",
        "OrdemProducao[_fimCriacao]": "",
        "OrdemProducao[_inicioEntrega]": f"{start_deliver_date}",
        "OrdemProducao[_fimEntrega]": f"{end_deliver_date}",
        "OrdemProducao[_limparFiltro]": "0",
        "pageSize": "20",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, data=login_payload) as response:
            if not response.ok:
                return None
            async with session.get(url, params=params) as response:
                if not response.ok:
                    return None
                data = await response.text()
                return format_carga_maquina_json_data_to_op(
                    data, start_deliver_date, end_deliver_date
                )


def test_fkapi_get() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_op_data_by_codigo("223536"))


def test_carga_maquina_get() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_op_data_on_carga_maquina())


if __name__ == "__main__":
    test_carga_maquina_get()
