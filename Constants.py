import base64

ORGANIZATION = "domoreexp"
PROJECT = "Teamspace"
personal_access_token = ""

base64_token = base64.b64encode(
    f":{personal_access_token}".encode("utf-8")
).decode("utf-8")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {base64_token}",
    "Accept": "application/json"
}

TGS_API_E2E_TESTS = "TGS API E2E tests"