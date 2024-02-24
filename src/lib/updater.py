import gc, ssl, wifi, socketpool, binascii, storage, os
import adafruit_requests

class UserPrint:
    def __init__(self):
        pass

    def do_print(self, s: str):
        pass

class UserIndicator:
    def __init__(self):
        pass
    
    def advance(self):
        pass

    def error(self):
        pass


class ReadonlyStorage(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class WifiUnreachable(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class WifiDisconnected(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class UnsupportedEncoding(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class SourceDirectoryNotFound(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message


class Updater:
    def __init__(self, ssid, wifipass, repo, branch="main", gh_token="", src_path="/", debug=False):
        self.debug = debug
        
        self.SSID = ssid
        self.WIFIPASS = wifipass

        self.HEADERS = {"Accept": "application/vnd.github+json"}
        if gh_token:
            self.HEADERS.update({"Authorization": "Bearer {}".format(gh_token)})
        self.HEADERS.update({"X-GitHub-Api-Version": "2022-11-28"})

        self.TREES_API_ENDPOINT = "/git/trees/"
        self.BLOBS_API_ENDPOINT = "/git/blobs/"

        self.GH_REPO = repo.replace("github.com/", "api.github.com/repos/")

        if not branch:
            self.GH_BRANCH = "main"
        else:
            self.GH_BRANCH = branch
        
        if not src_path:
            self.SRC_PATH = "/"
        else:
            self.SRC_PATH = src_path

        self.SPECIAL_FILES = ['lib/updater.py', 'boot.py']

        self.USER_PRINT = UserPrint()
        self.USER_INDICATOR = UserIndicator()


    def rprint(self, s, end='\n'):
        with open("updater_out.txt", "a") as f:
            f.write("{}{}".format(s, end))
    
        #print("{}".format(s), end=end)
        try:
            self.USER_PRINT.do_print("{}{}".format(s,end))
        except:
            # Do nothing if users function fails
            pass


    def dprint(self, s, end='\n'):
        if self.debug:
            with open("updater_out.txt", "a") as f:
                f.write("[D] {}{}".format(s, end))
            #print("[D] {}".format(s), end=end)
            try:
                self.USER_PRINT.do_print("[D] {}{}".format(s,end))
            except:
                # Do nothing if users function fails
                pass


    def check_storage(self):
        if storage.getmount('/').readonly != False:
            raise ReadonlyStorage("Volume mounted on '/' is not writable by circuitpython!")


    def delete_old_output(self):
        ST_MODE_FILE = 0x8000 #32768
        ST_MODE_DIR  = 0x4000 #16384

        try:
            st_mode = os.stat('updater_out.txt')[0]
            if st_mode == ST_MODE_FILE:
                os.remove('updater_out.txt')
            elif st_mode == ST_MODE_DIR:
                raise Exception("updater_out.txt is somehow a directory, dont do that! >:(")
            else:
                raise Exception("os.stat return unknown st_mode type!")
        except:
            return


    def connect_wifi(self):
        if wifi.radio.connected:
            return True

        # Try a few times
        for i in range(5):
            try:
                wifi.radio.connect(self.SSID, self.WIFIPASS)
                return wifi.radio.connected
            except:
                None

        return False


    def run(self):
        gc.enable()

        self.check_storage()
        self.delete_old_output()

        self.rprint("Trying to connect to wifi... ", end='')
        if self.connect_wifi():
            self.rprint("Success!")
        else:
            self.rprint("Failed :(")
            raise WifiUnreachable("Could not connect to wifi network '{}'".format(self.ssid))

        gc.collect()

        special_files = []

        pool = socketpool.SocketPool(wifi.radio)
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        self.rprint("[!] Starting update, do not restart badge!")

        src_tree_sha = self.get_src_tree(requests)
        
        gc.collect()

        src_tree = self.get_tree(requests, src_tree_sha, recursive=True).json()
        
        # Write files
        for i in src_tree["tree"]:
            if i["type"] == "blob":
                if i["path"] in self.SPECIAL_FILES:
                    special_files.append([i["path"] + '_tmp', i["path"]])
                    self.mkfile(requests, i["path"] + '_tmp', i["sha"])
                else:
                    self.mkfile(requests, i["path"], i["sha"])
        
        src_tree = None
        gc.collect()

        return special_files


    # Return user specified SRC tree hash
    def get_src_tree(self, request):
        # If SRC is root dir, just return GH_BRANCH
        if self.SRC_PATH == "" or self.SRC_PATH == "/":
            return self.GH_BRANCH
        
        # Find SRC directory in json structure
        root_tree = self.get_tree(request, self.GH_BRANCH, recursive=True).json()
        for i in root_tree["tree"]:
            if i["path"] == self.SRC_PATH:
                return i["sha"]

        # Cannot find src directory
        raise SourceDirectoryNotFound(f"Could not find source directory: {self.SRC_PATH}")


    # Make directory
    def mkdir(self, dir_path):
        ST_MODE_FILE = 0x8000 #32768
        ST_MODE_DIR  = 0x4000 #16384

        try:
            st_mode = os.stat(dir_path)[0]
            if st_mode == ST_MODE_DIR:
                return
            elif st_mode == ST_MODE_FILE:
                # TODO: what to do here?
                pass
            else:
                # Should never be here
                raise Exception("os.stat return unknown st_mode type!")
        except:
            self.dprint("{} does not exist yet".format(dir_path))

        dirs = list(filter(None, dir_path.split("/")))
        tmp_dir_path = ""

        for d in dirs:
            tmp_dir_path += "/" + d
            try:
                os.mkdir(tmp_dir_path)
                self.dprint("Created directory '{}'".format(dir_path))
            except OSError as e:
                # If OSError is not directory already existing
                if e.errno == 17:
                    self.dprint("Directory '{}' already exists".format(tmp_dir_path))
                else:
                    raise e


    # Write file, will overwrite files 
    def mkfile(self, requests, file_path, file_sha):
        file_contents = bytes()
        blob = self.get_blob(requests, file_sha).json()

        if blob["encoding"] == "base64":
            file_contents = binascii.a2b_base64(blob["content"])
        elif blob["encoding"] == "utf-8":
            file_contents = blob["content"].encode()
        else:
            raise UnsupportedEncoding("Encoding {} not recognized!".format(blob["encoding"]))

        # Create directory file should be in, if needed
        index = file_path.rfind('/')
        if index != -1:
            dir_path = file_path[:index]
            self.mkdir(dir_path)

        self.dprint("Writing {} now!".format(file_path))
        with open(file_path, "wb") as f:
            f.write(file_contents)


    # Returns blob data
    def get_blob(self, requests, hash):
        if not self.connect_wifi():
            raise WifiUnreachable("Lost connection to wifi network '{}'".format(self.ssid))

        endpoint = self.GH_REPO+self.BLOBS_API_ENDPOINT+hash
    
        self.dprint("Getting blob data from {}".format(endpoint))
        return requests.request("GET", endpoint, None, None, self.HEADERS)


    # Returns tree data
    def get_tree(self, requests, hash, recursive=False):
        if not self.connect_wifi():
            raise WifiUnreachable("Lost connection to wifi network '{}'".format(self.ssid))

        endpoint = self.GH_REPO+self.TREES_API_ENDPOINT+hash
        
        if recursive:
            endpoint += '?recursive=1'

        self.dprint("Getting tree data from {}".format(endpoint))
        return requests.request("GET", endpoint, None, None, self.HEADERS)