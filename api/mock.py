from fastapi import FastAPI, Response

from api.constants import TESTS_DIR
from api.utils import read_file

app = FastAPI()


@app.post("/gba-v/online/lo3services/adhoc")
async def mock_rvig():
    return Response(content=read_file(f"{TESTS_DIR}/rvig/999995571.xml"), media_type="application/xml")


# "at" is the actual query string required so we can't rename
@app.post("/bsn_attribute")
async def mock_inge6(at: str):  # pylint: disable=C0103
    print(at)
    return Response(
        content="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMUNDGq4KxM4U2Esz3zqoyjeVz/39vIpNeMFD8140", media_type="text/plain"
    )
