"""
Module containing functions to retrieve production order data from the CargaMaquina API.
Uses Pydantic models for validation and pure aiohttp for headless data extraction.
"""

import json
import re
import pathlib
import logging
from datetime import timedelta, datetime as dt
from typing import Dict, Optional
from bs4 import BeautifulSoup

from src.models.schema import OrdemDeProducao
from src.core.session_manager import SessionManager

TMP_PATH = pathlib.Path("./tmp")
TMP_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)


def format_carga_maquina_html_to_pydantic(
    html_content: str, start_date: str, end_date: str
) -> Optional[Dict[int, dict]]:
    """
    Parses the HTML table from CargaMaquina, converts rows into OrdemDeProducao
    Pydantic models, and saves them to a JSON file.
    """
    logging.info("Parsing CargaMaquina OP data via BeautifulSoup.")
    soup = BeautifulSoup(html_content, "html.parser")

    ops_dict: Dict[int, dict] = {}

    trs = soup.find_all("tr")
    if len(trs) <= 1:
        logging.warning("Nenhuma linha de OP encontrada no HTML retornado.")
        return None

    for tr in trs[1:]:
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue

        try:
            raw_code_text = tds[2].get_text(separator="", strip=True)
            raw_code = raw_code_text.split("-")[-1]
            code = int(re.sub(r"\D", "", raw_code))

            client = tds[3].get_text(separator="", strip=True)
            material_code = tds[4].get_text(separator="", strip=True)
            description = tds[5].get_text(separator="", strip=True)

            raw_qty = tds[6].get_text(separator="", strip=True).replace(".", "")
            quantity = int(raw_qty)

            op = OrdemDeProducao(
                code=code,
                material_code=material_code,
                client=client,
                description=description,
                quantity=quantity,
                box_count=1,
                weight=0,
            )

            ops_dict[op.code] = op.model_dump()

        except (ValueError, IndexError, AttributeError) as e:
            continue

    if not ops_dict:
        logging.warning("Falha ao extrair dados das OPs.")
        return None

    safe_start = start_date.replace("/", "-")
    safe_end = end_date.replace("/", "-")
    file_path = TMP_PATH / f"ordens_{safe_start}_{safe_end}.json"

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(ops_dict, file, indent=4, ensure_ascii=False)
        logging.info(
            f"Synchronization complete. Total OPs saved: {len(ops_dict)} at {file_path.name}"
        )
        return ops_dict
    except IOError as e:
        logging.error(f"Failed to write local JSON cache: {e}")
        return None


async def get_all_op_data_on_carga_maquina(
    session_manager: SessionManager,
) -> Optional[Dict[int, dict]]:
    """
    Fetches production orders data from CargaMaquina using an authenticated HTTP session.
    """
    if not session_manager.session:
        logging.error("HTTP Session not initialized. Please login first.")
        return None

    start_date = (dt.now() - timedelta(days=50)).strftime("%d/%m/%Y")
    end_date = (dt.now() + timedelta(days=50)).strftime("%d/%m/%Y")

    endpoint = f"{session_manager.base_url}/ordemProducao/exportarOrdens"

    headers = {
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{session_manager.base_url}/ordemProducao",
    }
    params = {
        "OrdemProducao[codigo]": "",
        "OrdemProducao[_nomeCliente]": "",
        "OrdemProducao[_nomeMaterial]": "",
        "OrdemProducao[status_op_id]": "Todos",
        "OrdemProducao[_etapasPlanejadas]": "",
        "OrdemProducao[forecast]": "0",
        "OrdemProducao[_inicioCriacao]": "",
        "OrdemProducao[_fimCriacao]": "",
        "OrdemProducao[_inicioEntrega]": start_date,
        "OrdemProducao[_fimEntrega]": end_date,
        "OrdemProducao[_limparFiltro]": "0",
        "pageSize": "10000",
    }

    try:
        logging.info(
            f"Starting OP data synchronization ({start_date} to {end_date})..."
        )

        async with session_manager.session.get(
            endpoint, params=params, headers=headers
        ) as response:
            response.raise_for_status()
            html_content = await response.text()

            return format_carga_maquina_html_to_pydantic(
                html_content, start_date, end_date
            )

    except Exception as e:
        logging.exception(f"Failed to fetch OP data: {e}")
        return None
