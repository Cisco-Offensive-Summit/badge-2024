from ssl import create_default_context
from wifi import radio as wifiradio
from socketpool import SocketPool
from binascii import a2b_base64
from storage import getmount
from adafruit_requests import Session
import gc, os


class UserPrint:
    def __init__(self):
        pass

    def do_print(self, s: str):
        pass

    def complete(self):
        pass

    def error(self):
        pass

class UserIndicator:
    def __init__(self):
        pass
    
    def advance(self):
        pass

    def complete(self):
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

class RepositoryUnreachable(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class RepositoryBadCredentials(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class SourceDirectoryNotFound(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message

class UnsupportedEncoding(Exception):
    def __init__(self, message):            
        super().__init__(message)
    def __str__(self):
        return self.message


class Updater:
    def __init__(self, ssid, wifipass, repo, branch="main", gh_token="", src_path="/", debug=False, mpy2py=False):
        self.debug = debug
        self.mpy2py = mpy2py
        
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


    def set_user_print_class(self, c):
        try:
            self.USER_PRINT = c()
            return True
        except:
            return False

    def set_user_indicator_class(self, c):
        try:
            self.USER_INDICATOR = c()
            return True
        except:
            return False

    def _trigger_user_print_do_print(self, s):
        try:
            self.USER_PRINT.do_print(s)
        except:
            pass
    
    def _trigger_user_print_complete(self):
        try:
            self.USER_PRINT.complete()
        except:
            pass
    
    def _trigger_user_print_error(self):
        try:
            self.USER_PRINT.error()
        except:
            pass

    def _trigger_user_indicator_advance(self):
        try:
            self.USER_INDICATOR.advance()
        except:
            pass
    
    def _trigger_user_indicator_complete(self):
        try:
            self.USER_INDICATOR.complete()
        except:
            pass

    def _trigger_user_indicator_error(self):
        try:
            self.USER_INDICATOR.error()
        except:
            pass


    def rprint(self, s, end='\n'):
        with open("updater_out.txt", "a") as f:
            f.write("{}{}".format(s, end))
    
        self._trigger_user_print_do_print("{}{}".format(s,end))


    def dprint(self, s, end='\n'):
        if self.debug:
            with open("updater_out.txt", "a") as f:
                f.write("[D] {}{}".format(s, end))
            #print("[D] {}".format(s), end=end)
            self._trigger_user_print_do_print("{}{}".format(s,end))


    def check_storage(self):
        if getmount('/').readonly != False:
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise ReadonlyStorage("Volume mounted on '/' is not writable by circuitpython!")


    def delete_old_output(self):
        ST_MODE_FILE = 0x8000 #32768
        ST_MODE_DIR  = 0x4000 #16384

        try:
            st_mode = os.stat('updater_out.txt')[0]
            if st_mode == ST_MODE_FILE:
                os.remove('updater_out.txt')
            elif st_mode == ST_MODE_DIR:
                self._trigger_user_print_error()
                self._trigger_user_indicator_error()
                raise Exception("updater_out.txt is somehow a directory, dont do that! >:(")
            else:
                self._trigger_user_print_error()
                self._trigger_user_indicator_error()
                raise Exception("os.stat return unknown st_mode type!")
        except:
            return


    def handle_response_code(self, req):
        # Catch non 200 responses
        if req.status_code == 200:
            return
        if req.status_code == 404:
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise RepositoryUnreachable("Unable to access repository.\nStatus: {}\n{}".format(req.status_code, req.text))
        if req.status_code == 401:
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise RepositoryBadCredentials("Bad credentials supplied for repository.\nStatus: {}\n{}".format(req.status_code, req.text))
        else:
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise Exception("Recieved non 200 response from Repository.\nStatus: {}\n{}".format(req.status_code, req.text))


    def connect_wifi(self):
        if wifiradio.connected:
            return True

        # Try a few times
        for i in range(5):
            try:
                wifiradio.connect(self.SSID, self.WIFIPASS)
                return wifiradio.connected
            except:
                None

        return False


    def run(self):
        gc.enable()

        self.dprint("Mem free: {}".format(gc.mem_free()))

        self.check_storage()
        self.delete_old_output()
        self._trigger_user_indicator_advance()

        self.rprint("Trying to connect to wifi... ", end='')
        if self.connect_wifi():
            self.rprint("Success!")
        else:
            self.rprint("Failed :(")
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise WifiUnreachable("Could not connect to wifi network '{}'".format(self.SSID))
        self._trigger_user_indicator_advance()

        gc.collect()

        special_files = []

        pool = SocketPool(wifiradio)
        requests = Session(pool, create_default_context())
        self._trigger_user_indicator_advance()

        gc.collect()

        self.rprint("[!] Starting update, do not restart badge!")

        src_tree_sha = self.get_src_tree(requests)
        self._trigger_user_indicator_advance()
        
        gc.collect()

        src_tree_req = self.get_tree(requests, src_tree_sha, recursive=True)
        self._trigger_user_indicator_advance()
        
        gc.collect()

        # If response code is not 200, throw exception
        self.handle_response_code(src_tree_req)

        src_tree = src_tree_req.json()
        
        gc.collect()

        # Write files
        for i in src_tree["tree"]:
            if i["type"] == "blob":
                if i["path"] in self.SPECIAL_FILES:
                    special_files.append([i["path"] + '_tmp', i["path"]])
                    self.mkfile(requests, i["path"] + '_tmp', i["sha"])
                else:
                    self.mkfile(requests, i["path"], i["sha"])

                self._trigger_user_indicator_advance()
                gc.collect()
        
        src_tree_req.close()
        del src_tree_req
        del src_tree
        gc.collect()

        self._trigger_user_indicator_complete()
        self._trigger_user_print_complete()

        return special_files


    # Return user specified SRC tree hash
    def get_src_tree(self, request):
        # If SRC is root dir, just return GH_BRANCH
        if self.SRC_PATH == "" or self.SRC_PATH == "/":
            return self.GH_BRANCH
        
        self.dprint("Finding source path {} in branch {}.".format(self.SRC_PATH, self.GH_BRANCH))
        # Find SRC directory in json structure
        root_tree_req = self.get_tree(request, self.GH_BRANCH, recursive=False)

        # If response code is not 200, throw exception
        self.handle_response_code(root_tree_req)

        root_tree = root_tree_req.json()
        for i in root_tree["tree"]:
            if i["path"] == self.SRC_PATH:
                return i["sha"]

        # Cannot find src directory
        self._trigger_user_print_error()
        self._trigger_user_indicator_error()
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
                self._trigger_user_print_error()
                self._trigger_user_indicator_error()
                raise Exception("Cannot make directory {} it already exists as a file?!".format(dir_path))
                pass
            else:
                # Should never be here
                self._trigger_user_print_error()
                self._trigger_user_indicator_error()
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
                    self._trigger_user_print_error()
                    self._trigger_user_indicator_error()
                    raise e


    # Write file, will overwrite files 
    def mkfile(self, requests, file_path, file_sha):
        file_contents = bytes()
        blob_req = self.get_blob(requests, file_sha)
        
        try:
            self.handle_response_code(blob_req)
        except RepositoryUnreachable as e:
            self.drpint("Could not download file {}.\n {}".format(file_path, e))
            return

        blob = blob_req.json()
        blob_req.close()
        del blob_req
        gc.collect()

        if blob["encoding"] == "base64":
            file_contents = a2b_base64(blob["content"])
        elif blob["encoding"] == "utf-8":
            file_contents = blob["content"].encode()
        else:
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise UnsupportedEncoding("Encoding {} not recognized!".format(blob["encoding"]))

        # Create directory file should be in, if needed
        index = file_path.rfind('/')
        if index != -1:
            dir_path = file_path[:index]
            self.mkdir(dir_path)

        self.dprint("Writing {} now!".format(file_path))
        with open(file_path, "wb") as f:
            f.write(file_contents)
        
        # If new file is .py delete old .mpy
        # If new file is .mpy delete old .py
        if self.mpy2py:
            split = file_path.rsplit('.', 1)
            if len(split) < 2:
                return
            if split[1] == "py":
                try:
                    st_mode = os.stat(split[0]+'.mpy')[0]
                    if st_mode == 0x8000:
                        self.dprint("Deleting file {}".format(split[0]+'.mpy'))
                        os.remove(split[0]+'.mpy')
                except:
                    return
            elif split[1] == "mpy":
                try:
                    st_mode = os.stat(split[0]+'.py')[0]
                    if st_mode == 0x8000:
                        self.dprint("Deleting file {}".format(split[0]+'.py'))
                        os.remove(split[0]+'.py')
                except:
                    return
            else:
                return


    # Returns blob data
    def get_blob(self, requests, hash):
        if not self.connect_wifi():
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise WifiUnreachable("Lost connection to wifi network '{}'".format(self.ssid))

        endpoint = self.GH_REPO+self.BLOBS_API_ENDPOINT+hash
    
        self.dprint("Getting blob data from {}".format(endpoint))
        return requests.request("GET", endpoint, None, None, self.HEADERS)


    # Returns tree data
    def get_tree(self, requests, hash, recursive=False):
        if not self.connect_wifi():
            self._trigger_user_print_error()
            self._trigger_user_indicator_error()
            raise WifiUnreachable("Lost connection to wifi network '{}'".format(self.ssid))

        endpoint = self.GH_REPO+self.TREES_API_ENDPOINT+hash
        
        if recursive:
            endpoint += '?recursive=1'

        self.dprint("Getting tree data from {}".format(endpoint))
        return requests.request("GET", endpoint, None, None, self.HEADERS)