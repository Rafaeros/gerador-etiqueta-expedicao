"""
This module contains functions to get data from the web or APIs
"""

import re
import json
import pathlib
import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import timedelta, datetime as dt
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from core.requests_api_go import fkapi_get_op_data_by_codigo

TMP_PATH = "./tmp/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)


@dataclass
class OrdemDeProducao:
    """Class to represents a production order."""

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
        """
        Extracts the client code from the description and stores it in the client_code attribute.

        Uses a regular expression to search for a string enclosed in parentheses in the description.
        If a match is found, the enclosed string is stored in the client_code
        attribute. If no match is found, the attribute is set to an empty string.
        """
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
        """
        Updates the barcode attribute based on the client_code attribute.

        If the client_code attribute is not empty, the barcode is updated
        with the material_code and client_code.
        The new barcode is formatted as "material_code (client_code)".

        :return: None
        """
        if self.client_code == "":
            return
        self.barcode = f"{self.material_code} ({self.client_code})"


class OrdensDeProducao:
    """
    Class to create a list of isntances of OrdemDeProducao
    """

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
        """
        Creates a new instance of OrdemDeProducao and stores it in the
        OrdensDeProducao.instances dictionary.

        Args:
            code (int): The code of the OP.
            material_code (str): The material code of the OP.
            client (str): The client of the OP.
            description (str): The description of the OP.
            barcode (str): The barcode of the OP.
            quantity (int): The quantity of the OP.
            box_count (int): The box count of the OP.
            weight (int): The weight of the OP.
        """
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
        """
        Returns a dictionary with all the instances of OrdemDeProducao.

        The keys of the dictionary are the codes of the OPs and the values are dictionaries
        with the attributes of the OP.

        :return: A dictionary with all the OPs
        """
        return cls.instances

    @classmethod
    def find_by_codigo(cls, code) -> dict[int, int]:
        """
        Finds an OrdemDeProducao instance by its code.

        :param code: The code of the OP.
        :return: The OP instance if found, None otherwise.
        """
        return cls.instances.get(code, None)


def format_carga_maquina_json_data_to_op(
    raw: str, start_deliver_date: str, end_deliver_date: str
) -> str | None:
    """
    Formats the CargaMaquina data into the OP format.

    Receives the raw string from the CargaMaquina page and the delivery dates and
    returns a string in JSON format with the OPs, or None if it is not possible
    to format the data.

    :param raw: The string with the CargaMaquina page
    :param start_deliver_date: The initial delivery date
    :param end_deliver_date: The final delivery date
    :return: A string in JSON format with the OPs, or None
    """
    logging.info("Formating CargaMaquina OP data")
    soup = BeautifulSoup(raw, "html.parser")
    trs = soup.find_all("tr")[1:]
    for tr in trs:
        code: int = (
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
        f"{TMP_PATH}ordens_{start_deliver_date}_{end_deliver_date}.json",
        "w",
    ) as file:
        json.dump(OrdensDeProducao.get_instances(), file, indent=4, ensure_ascii=False)
        return json_string
    return None


async def get_login_cookies(login_url: str) -> dict[str, str]:
    """
    Get the login cookies using selenium.

    Args:
    - login_url: str - The login URL of the application.

    Returns:
    - dict[str, str] - A dictionary with the cookies.
    """
    logging.info("Trying to get login cookies with selenium")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options)
    try:
        driver.get(login_url)
        driver.find_element(By.ID, "LoginForm_username").send_keys("")
        driver.find_element(By.ID, "LoginForm_password").send_keys("")
        driver.find_element(By.NAME, "yt0").click()
        cookies = driver.get_cookies()
    except NoSuchElementException as e:
        logging.error("Error to get login cookies: %s", e)
        return {}
    finally:
        driver.quit()
    cookies = {cookie["name"]: cookie["value"] for cookie in cookies}
    return cookies


async def get_op_data_by_codigo(codigo_ordem_producao: str) -> OrdemDeProducao | None:
    """
    Get the production order data by code from Go API.

    Args:
    - codigo_ordem_producao: str - The code of the production order.

    Returns:
    - OrdemDeProducao | None - The production order data, or None if an error occurs.
    """
    logging.info("Trying to get OP data from API")
    try:
        op_data: dict = await fkapi_get_op_data_by_codigo(codigo_ordem_producao)
        if op_data is None:
            logging.info("Error to get data on API")
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
        logging.error("Error to decode Json data on API")
        return None


async def get_all_op_data_on_carga_maquina() -> dict | None:
    """
    Get all production orders data from CargaMaquina with the given parameters.

    This function will use the cookies obtained from the login page to get the
    production orders data from the CargaMaquina page. The parameters are used
    to filter the data and get the desired production orders.

    The data will be formatted into the OP format and returned as a dictionary.

    Args:
    - None

    Returns:
    - dict | None - The production orders data, or None if an error occurs.
    """
    login_url: str = "https://app.cargamaquina.com.br/site/login/c/31.1~78,8%5E56,8"
    cookies: list[dict] = await get_login_cookies(login_url)
    logging.info("Cookies get successfully")
    start_deliver_date: str = (dt.now() - timedelta(days=50)).strftime("%d/%m/%Y")
    end_deliver_date: str = (dt.now() + timedelta(days=50)).strftime("%d/%m/%Y")
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
    logging.info("Trying to get OP data from CargaMaquina with cookies")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies) as response:
            if not response.ok:
                logging.error("Error to get data on CargaMaquina with cookies")
                return None
            data = await response.text()
            logging.info("Data get successfully on CargaMaquina")
            return format_carga_maquina_json_data_to_op(
                data, start_deliver_date, end_deliver_date
            )


def test_fkapi_get() -> None:
    """
    Test the fkapi_get_op_data_by_codigo function.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_op_data_by_codigo("223536"))


def test_carga_maquina_get() -> None:
    """
    Test the get_all_op_data_on_carga_maquina function.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_op_data_on_carga_maquina())


if __name__ == "__main__":
    test_carga_maquina_get()
