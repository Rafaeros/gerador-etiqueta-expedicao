import re
from typing import Union
from pydantic import BaseModel, Field, model_validator

class OrdemDeProducao(BaseModel):
    """
    Pydantic model representing a Production Order (OP).
    Automatically extracts the client code from the description and formats the barcode.
    """
    code: int
    material_code: str
    client: str
    description: str
    quantity: int
    box_count: int = Field(default=1, ge=1)
    weight: Union[int, str] = 0
    
    client_code: str = ""
    barcode: str = ""

    @model_validator(mode='after')
    def extract_and_format_codes(self) -> 'OrdemDeProducao':
        match = re.search(r"\((.*?)\)", self.description)
        if match:
            raw_client_code = match.group(1).strip()
            if self.client.upper().startswith("TRUCKS") and raw_client_code.upper().startswith("TRUCKS"):
                self.client_code = raw_client_code.split(":")[-1].strip()
            else:
                self.client_code = raw_client_code
                
            self.description = re.sub(r"\s*\(.*?\)", "", self.description).strip()
        
        if self.client_code:
            self.barcode = f"{self.material_code} ({self.client_code})"
        else:
            self.barcode = self.material_code
            
        return self