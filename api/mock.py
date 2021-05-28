from fastapi import FastAPI, Response

from api.constants import TESTS_DIR
from api.utils import read_file

app = FastAPI()


@app.post("/cibg.sbv.testtool.webservice.dec14/opvragenpersoonsgegevens.asmx")
async def mock_sbvz():
    return Response(
        content=read_file(f"{TESTS_DIR}/sbvz/direct_match_correct_response.xml"), media_type="application/xml"
    )
