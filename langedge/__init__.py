import langedge.api
import langedge.credential


API_URL = "https://api.gengo.com/v2"


class Gengo:
    def __init__(self, public_key: str, private_key: str) -> None:
        credential = langedge.credential.Credential(API_URL, public_key, private_key)
        self.account = langedge.api.Account(credential)
        self.job = langedge.api.Job(credential)
