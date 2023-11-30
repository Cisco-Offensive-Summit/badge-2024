import board, secrets, gc, flavortext
import ipaddress, ssl, wifi, socketpool, adafruit_requests

HEADERS = {"Accept": "application/vnd.github+json"}
if secrets.GH_TOKEN:
    HEADERS.update({"Authorization": "Bearer {}".format(secrets.GH_TOKEN)})
HEADERS.update({"X-GitHub-Api-Version": "2022-11-28"})

TREES_API_ENDPOINT = "/git/trees/"
BLOBS_API_ENDPOINT = "/git/blobs/"

secrets.GH_REPO = secrets.GH_REPO.replace("github.com/", "api.github.com/repos/")

# Main app entrypoint
def run():

    gc.enable()
    
    print("Trying to connect to wifi... ", end='')
    if connect_wifi():
        print("Success!")
    else:
        print("Failed :(")
        return
    
    gc.collect()

    print("[!] Starting update, do not restart badge!")
    if update():
        print("[!] Update successful!")
    else:
        print("[!] Update Failed :(")
        return

    gc.collect()


def connect_wifi():
    if wifi.radio.connected:
        return True
    
    if not secrets.WIFI_NETWORK:
        return False

    for i in range(5):
        try:
            wifi.radio.connect(secrets.WIFI_NETWORK, secrets.WIFI_PASS)
            return wifi.radio.connected
        except:
            None
    
    return False


def update():
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    response = get_tree(requests, secrets.GH_BRANCH)
    print(response.json())


def get_tree(requests, branch):
    print(secrets.GH_REPO+TREES_API_ENDPOINT+branch)
    return requests.request("GET", secrets.GH_REPO+TREES_API_ENDPOINT+branch, None, None, HEADERS)