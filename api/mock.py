from fastapi import FastAPI, Response

from api.constants import TESTS_DIR
from api.utils import read_file

app = FastAPI()


@app.post("/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx")
async def mock_sbvz():
    return Response(
        content=read_file(f"{TESTS_DIR}/sbvz/direct_match_correct_response.xml"), media_type="application/xml"
    )


@app.post("/bsn_attribute")
async def mock_inge6(at: str):
    print(at)
    return Response(
        content="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzpEliQZGIthee86WIg0w599yMlSzcg8ojyA==", media_type="text/plain"
    )
