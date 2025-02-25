import os
import uvicorn
from fastapi import FastAPI, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from configparser import ConfigParser
import requests

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
UVICORN_HOST = get_os_variable('UVICORN_HOST')
URL_CERT = get_os_variable('URL_CERT')

security = HTTPBearer()
app = FastAPI()


def get_response(url: str) -> JSONResponse:
    """
    Получает ответ
    """
    try:
        session = requests.Session()

        # session.auth = (USER, PASSWORD)

        # session.verify = URL_CERT

        response = session.post('https://nio-eusb-01.gksm.local:8000/api/core/auth',
                                data='{"username":"' + USER + '","password":"' + PASSWORD + '","mode":"normal"}',
                                verify=False)

        response = session.get(url,
                               verify=False)

        session.close()
        return response.json()

    except Exception as e:
        print(str(e))
        return JSONResponse(status_code=501,
                            content={"error": str(e)})


@app.get("/")
async def root():
    return {"service available"}


@app.get("/config")
async def message(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(url='https://url/config')


@app.get("/sn")
async def message(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(url='https://url/get/sn')


@app.get("/usbinfo")
async def message(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != TOKEN:
        return JSONResponse(status_code=401, content="Not authenticated")
    return get_response(url='https://url/usbinfo')


uvicorn.run(app, host=UVICORN_HOST, port=2620)
