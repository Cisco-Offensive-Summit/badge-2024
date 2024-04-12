import json
import os

from .fileops import is_dir, is_file
from .log import log

APPS_DIR = "/apps"
DEFAULT_ICON = "/badge/img/app-default.bmp"


class App:
    def __init__(self, appdir):
        self.appdir = appdir

    @property
    def code_file(self):
        code_file = f"{self.appdir}/code.py"
        if not is_file(code_file):
            return None
        return code_file

    @property
    def icon_file(self):
        icon_file = f"{self.appdir}/icon.bmp"
        if not is_file(icon_file):
            icon_file = DEFAULT_ICON
        return icon_file

    @property
    def metadata_file(self):
        metadata_file_path = f"{self.appdir}/metadata.json"
        if not is_file(metadata_file_path):
            return None
        return metadata_file_path

    @property
    def metadata_json(self):
        metadata_file_path = self.metadata_file
        if not metadata_file_path:
            raise Exception("Metadata file not found")
        with open(metadata_file_path) as f:
            metadata = json.load(f)

        return metadata

    @property
    def boot_config(self):
        boot_json_file = f"{self.appdir}/boot.json"
        try:
            return json.load(open(boot_json_file, "r"))
        except Exception:
            # log(f"App.boot_config err\n{repr(e)}")
            return None

    @property
    def app_name(self):
        return self.appdir.split('/')[::-1][0]

    def __repr__(self):
        s = f"App({self.code_file},icon={self.icon_file})"
        if self.boot_config:
            s += ",boot_config=True"
        return s


def get_app_list():
    entries = list()
    if not is_dir(APPS_DIR):
        log("APPS_DIR not directory")
        return entries
    for e in os.listdir(APPS_DIR):
        # Hide an app by renaming it's directory to start with '_'
        # XXX: hack for dev
        if e.startswith("_"):
            continue
        app_path = f"{APPS_DIR}/{e}"
        if is_dir(app_path):
            app = App(app_path)
            entries.append(app)
    return entries


# APPLIST = [App(c, icon_file=i) for c, i in discover_app_files()]
APPLIST = get_app_list()
# log("badge.apps", APPLIST)
