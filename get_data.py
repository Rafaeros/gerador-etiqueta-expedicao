""" Module that contains the Label data to generate the label. """

from datetime import datetime as dt
import re
import pandas as pd

file_date = dt.now().strftime("%d_%m_%Y")

# Class LabelInfo
class LabelInfo:
    """ LabelInfo class that contains information about the label. """

    def __init__(self,
                 op: str,
                 client: str,
                 code: str,
                 description: str,
                 quantity: int,
                 boxes: int,
                 weight: int) -> None:
        """ Initialize the LabelInfo class. """
        today: str = dt.now()
        self.date: str = today.strftime("%d/%m/%Y")
        self.mwm_date: str = today.strftime("%Y%m%d")
        self.op: str = op
        self.client: str = client
        self.code: str = code
        self.barcode: str = ""
        self.client_code: str = ""
        self.description: str = description
        self.quantity: int = quantity
        self.weight: int = weight
        self.boxes: int = boxes
        self.set_barcode_data()

    def get_client_code(self, text: str) -> str:
        """ Get the client code from the description. """
        search = re.search(r'\((.*?)\)', text)
        if search:
            return search.group(1)
        return ''

    def set_barcode_data(self) -> str:
        """ Set the barcode data. """
        self.client_code = self.get_client_code(self.description)
        self.barcode = self.code + " " + f"({self.client_code})"
        return self.barcode


class LabelData:
    """LabelData class that contains information about the production orders to generate label."""

    def __init__(self, file_path: str = f"./ordens_{file_date}.xlsx") -> None:
        """ Initialize the LabelData class. """
        self.file_path: str = file_path
        self.label_data: pd.DataFrame = self.load_data(self.file_path)
        self.format_data()

    def load_data(self, file_path: str) -> pd.DataFrame | None:
        """ Load the data from the file. """
        try:
            return pd.read_excel(file_path)
        except FileNotFoundError:
            print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
            return None
        except ValueError:
            print(f"O arquivo '{
                  file_path}' não possui um formato compatível ou está corrompido.")
            return None

    def format_data(self) -> None:
        """Format the data. to remove unnecessary columns."""
        self.label_data = self.label_data[
            [
                'Código',
                'Cliente',
                'Cód. Material',
                'Material',
                'Quantidade'
            ]
        ]

    def print_data(self) -> None:
        """Print the data."""
        print(self.label_data)

    def get_data(self, op: str, boxes: int, kg: str) -> LabelInfo | None:
        """ Get the data for the label. by production order code"""
        try:
            current_data = self.label_data.loc[
                self.label_data['Código'] == op,
                ['Cliente', 'Cód. Material', 'Material', 'Quantidade']
            ]
            current_label = LabelInfo(
                op,
                current_data.loc[:, ['Cliente']].to_string(
                    index=False, header=False),
                current_data.loc[:, ['Cód. Material']].to_string(
                    index=False, header=False),
                current_data.loc[:, ['Material']].to_string(
                    index=False, header=False),
                current_data.loc[:, ['Quantidade']].to_string(
                    index=False, header=False),
                boxes,
                kg
            )
            return current_label
        except ValueError as e:
            print(e)
