import os
import uvicorn
from fastapi import FastAPI, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from configparser import ConfigParser
import requests
import re
from loki_logging_lib import loki_handler

URL_CONF = 'config/config.ini'


def get_os_variable(name):
    """
    Получает значение переменной окружения или из конфигурационного файла.
    :param name: Имя переменной.
    :return: Значение переменной.
    """
    try:
        config = ConfigParser()
        config.read(URL_CONF)
        return config['config'][name]
    except KeyError:
        return os.environ[name]


TOKEN = get_os_variable('TOKEN')
USER = get_os_variable('USER')
PASSWORD = get_os_variable('PASSWORD')
LOKI_URL = get_os_variable('LOKI_URL')
LOKI_JOB_NAME = get_os_variable('LOKI_JOB_NAME')
UVICORN_HOST = get_os_variable('UVICORN_HOST')
URL_CERT = get_os_variable('URL_CERT')

security = HTTPBearer()
app = FastAPI()

logger = loki_handler.setup_logger(loki_url=LOKI_URL,
                                   service_name=LOKI_JOB_NAME)


def check_host(host: str) -> bool:
    if re.fullmatch(r'^nio[a-zA-Z0-9\-]+.gksm.local', host):
        return True
    else:
        return False


def get_response(host: str, url_postfix: str) -> JSONResponse:
    """
    Получает ответ
    """

    if not check_host(host):
        return JSONResponse(status_code=200, content='Wrong Host')

    try:
        session = requests.Session()

        # session.auth = (USER, PASSWORD)

        # session.verify = URL_CERT

        url_auth = 'https://'+host+':8000/api/core/auth'

        url = 'https://'+host+':8000'+url_postfix

        response = session.post(url_auth,
                                data='{"username":"' + USER + '","password":"' + PASSWORD + '","mode":"normal"}',
                                verify=False)

        response = session.get(url,
                               verify=False)

        session.close()
        return response.json()

    except Exception as e:
        logger.error(str(e))
        return JSONResponse(status_code=501,
                            content={"error": str(e)})


@app.get("/")
async def root():
    return {"service available"}


@app.get("/config")
async def message(host: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(host=host, url_postfix='/api/nioeusb/config')


@app.get("/sn")
async def message(host: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(host=host, url_postfix='/api/nioeusb/get/sn')


@app.get("/usbinfo")
async def message(host: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(host=host, url_postfix='/api/nioeusb/usbinfo')


uvicorn.run(app, host=UVICORN_HOST, port=2620)
