import board, secrets, gc, flavortext
import ipaddress, ssl, wifi, socketpool, adafruit_requests
import binascii, storage

HEADERS = {"Accept": "application/vnd.github+json"}
if secrets.GH_TOKEN:
    HEADERS.update({"Authorization": "Bearer {}".format(secrets.GH_TOKEN)})
HEADERS.update({"X-GitHub-Api-Version": "2022-11-28"})

TREES_API_ENDPOINT = "/git/trees/"
BLOBS_API_ENDPOINT = "/git/blobs/"

secrets.GH_REPO = secrets.GH_REPO.replace("github.com/", "api.github.com/repos/")
if not secrets.GH_BRANCH:
    secrets.GH_BRANCH = "main"

debug_print = False

def dprint(s):
    if debug_print:
        print("[D] {}".format(s))


# Main app entrypoint
def run(debug=False):

    global debug_print
    debug_print = debug

    if not secrets.GH_BRANCH:
        print("[X] Please specify git repo to pull from") 

    gc.enable()
    
    print("Trying to connect to wifi... ", end='')
    if connect_wifi():
        print("Success!")
    else:
        print("Failed :(")
        return
    
    gc.collect()

    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    print("[!] Starting update, do not restart badge!")

    try:
        src_sha = get_src_tree(requests, secrets.GH_SRC_FOLDER)
    except Exception as e:
        print("[X] Update Failed")
        print("[X] {}".format(e))
        return

    dprint("Found source SHA for {}: {}".format(secrets.GH_SRC_FOLDER, src_sha))

    gc.collect()

    print("[I] Gathering info on files to update.")

    try:
        files = get_all_files(requests, src_sha, "")
    except Exception as e:
        print("[X] Update Failed")
        print("[X] {}".format(e))
        return

    dprint("Files: {}".format(files))

    for (path, sha) in files:
        print("[I] Updating file {}".format(path))
        try:
            blob = update_file(requests, path, sha)
        except Exception as e:
            print("[X] Update Failed")
            print("[X] {}".format(e))
            return
        

# Connect to wifi
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

# Write file to disk
def update_file(requests, file_path, file_sha):
    file_contents = bytes()
    blob = get_blob(requests, file_sha).json()
    
    if blob["encoding"] == "base64":
        file_contents = binascii.a2b_base64(blob["content"])
    elif blob["encoding"] == "utf-8":
        file_contents = blob["content"].encode()
    else:
        raise Exception("Encoding {} not recognized!".format(blob["encoding"]))

    dprint("Writing {} now!".format(file_path))
    with open(file_path, "wb") as f:
        f.write(file_contents)
    

# Get list of files to request and their paths
def get_all_files(requests, tree_sha, pre_path):
    files = []
    trees = []

    if pre_path != "":
        pre_path = pre_path + "/"

    dprint("Gathering data about path \'{}\'".format(pre_path))

    # Get file current depth blob and tree info
    tree_data = get_tree(requests, tree_sha).json()
    for i in tree_data["tree"]:
        if i["type"] == "blob":
            dprint("Adding file: {} to list".format(pre_path + i["path"]))
            files.append((pre_path + i["path"], i["sha"]))
        elif i["type"] == "tree":
            dprint("Adding tree: {} to list".format(pre_path + i["path"]))
            trees.append((i["sha"], i["path"]))
        
    # Recurse through found trees
    for (sha, path) in trees:
        files.extend(get_all_files(requests, sha, pre_path + path))
    
    return files

# Get the SHA hash of the src tree of our code
def get_src_tree(requests, src_path):
    src_sha = None
    tree = get_tree(requests, secrets.GH_BRANCH).json()

    if src_path == "" or src_path == "/":
        return tree["sha"]

    dprint("Searching for source path: {}".format(src_path))
    for s in src_path.split("/"):
        dprint("Looking for tree {}".format(s))
        dprint(tree)
        src_sha = None

        for t in tree["tree"]:
            if t["type"] == "tree" and t["path"] == s:
                src_sha = t["sha"]
        
        if src_sha == None:
            raise Exception("Source tree '{}' not found in repository".format(src_path))
        
        tree = get_tree(requests, src_sha).json()

    # Should never happen, but keeping this here
    if not src_sha:
        raise Exception("Source tree '{}' not found in repository".format(src_path))
    
    return src_sha


# Returns tree data
def get_tree(requests, hash):
    # If nothing is specified use main branch
    if hash == "":
        hash = "main"
    
    endpoint = secrets.GH_REPO+TREES_API_ENDPOINT+hash
    
    dprint("Getting tree data from {}".format(endpoint))
    return requests.request("GET", endpoint, None, None, HEADERS)


# Returns blob data
def get_blob(requests, hash):
    endpoint = secrets.GH_REPO+BLOBS_API_ENDPOINT+hash
    
    dprint("Getting blob data from {}".format(endpoint))
    return requests.request("GET", endpoint, None, None, HEADERS)