import os
from typing import List
import requests
from pydantic import BaseModel


class IpModel(BaseModel):
    ip: str
    city: str
    region: str
    country: str
    loc: str
    org: str
    postal: str
    timezone: str

    @property
    def get_results(self) -> str:
        return (
            f"IP: {self.ip}\n"
            f"City: {self.city}\n"
            f"Region: {self.region}\n"
            f"Country: {self.country}\n"
            f"Location: {self.loc}\n"
            f"Organisation: {self.org}\n"
            f"Postal: {self.postal}\n"
            f"Timezone: {self.timezone}\n"
        )


class Data:
    categories: List[str] = []
    xtream_account = None
    selected_list: List[str]
    channels: List[str]
    media_instance: str
    filename: str = os.path.join(os.getcwd(), "programs.py")
    ip_info = requests.get("http://ipinfo.io/json").json()
