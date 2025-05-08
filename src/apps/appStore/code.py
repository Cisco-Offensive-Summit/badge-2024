from badge.wifi import WIFI
from badge.log import log
from badge.utils import download_file
import secrets

wifi = WIFI()

def request_app_list():
    if wifi.connect_wifi():
        GET_APP_LIST = 'badge/list_apps'
        url = wifi.host + GET_APP_LIST
        method = 'GET'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        body = {
            'uniqueID' : secrets.UNIQUE_ID
        }
        try:
            rsp = wifi.requests(method=method, url=url, json=body, headers=headers)
            body = rsp.json()
        except RequestError as e:
            print("Request error:", e)
        except NetworkError as e:
            print("Network error:", e)
        except (OSError, RuntimeError, ValueError) as e:
            print("General connection failure:", e)
        return body['apps']

    # Couldn't connect wifi
    else:
        log("Couldn't connect to wifi")

def get_app_files(app_name:str):
    if wifi.connect_wifi():
        GET_APP = 'badge/get_app'
        url = wifi.host + GET_APP
        method = 'GET'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        body = {
            'app_name' : app_name,
            'uniqueID' : secrets.UNIQUE_ID
        }
        try:
            rsp = wifi.requests(method=method, url=url, json=body, headers=headers)
            body = rsp.json()
        except RequestError as e:
            print("Request error:", e)
        except NetworkError as e:
            print("Network error:", e)
        except (OSError, RuntimeError, ValueError) as e:
            print("General connection failure:", e)
        return body['files']

    # Couldn't connect wifi
    else:
        log("Couldn't connect to wifi")

    pass

def download_app(download_files:list):
    for file in download_files:
        if not download_file(file, wifi):
            log(f"Download failed {file}")
            return False
    
    return True

def ask_user(app_list:list) -> str:
    return app_list[1]

def get_app_data():
    pass

def main():
    app_list = request_app_list()
    app_name = ask_user(app_list)
    download_files = get_app_files(app_name)
    complete = download_app(download_files)


#main()