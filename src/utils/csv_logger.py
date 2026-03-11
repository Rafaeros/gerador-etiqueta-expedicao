import csv
import pathlib
import logging
from datetime import datetime

from src.models.schema import OrdemDeProducao

# CWD relative or safe path
LOGS_DIR = pathlib.Path(__file__).parent.parent.parent / "tmp" / "logs"


def log_print_action(op: OrdemDeProducao, label_count: int, is_manual_weight: bool):
    """
    Logs the printed label details to a CSV file.
    """
    try:
        # Create directory if it doesn't exist
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # General CSV for print history
        csv_file = LOGS_DIR / "print_logs.csv"

        file_exists = csv_file.exists()

        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            fieldnames = [
                "Data/Hora",
                "Número da OP",
                "Código do Produto",
                "Código do Cliente",
                "Cliente",
                "Descrição",
                "Quantidade Total",
                "Peso",
                "Peso Manual?",
                "Quantidade de Etiquetas (Caixas)",
            ]

            # Using semicolon delimiter for better Excel compatibility in pt-BR
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Número da OP": op.code,
                    "Código do Produto": op.material_code,
                    "Código do Cliente": op.client_code,
                    "Cliente": op.client,
                    "Descrição": op.description,
                    "Quantidade Total": op.quantity,
                    "Peso": op.weight,
                    "Peso Manual?": "Sim" if is_manual_weight else "Não",
                    "Quantidade de Etiquetas (Caixas)": label_count,
                }
            )
            logging.info(f"Registered print log for OP {op.code}.")
    except Exception as e:
        logging.error(f"Error writing to print log: {e}")
