import os

ST_DIR = 0x4000
ST_FILE = 0x8000


def st_mode(path):
    return os.stat(path)[0]


def is_dir(path):
    try:
        return st_mode(path) == ST_DIR
    except OSError:
        return False


def is_file(path):
    try:
        return st_mode(path) == ST_FILE
    except OSError:
        return False

def freespace():
    os.sync()
    (f_bsize, 
     f_frsize, 
     f_blocks, 
     f_bfree, 
     f_bavail, 
     f_files, 
     f_ffree, 
     f_favail, 
     f_flag, 
     f_namemax) = os.statvfs("/")

    size = f_blocks * f_frsize    
    free = f_bfree * f_bsize
    used = size - free
    return (size, used, free)

def diskspace_str():
    size_k, used_k, free_k = [ f"{n//1024}" for n in freespace() ]
    return f"{used_k}/{size_k}K"


# def can_write():
#     did_write = False
#     test_file = "/.test-write"
#     try:
#         with open(test_file, "wb") as f:
#             f.write("testing writeable")
#             f.flush()
#         os.remove(test_file)
#     except OSError:
#         did_write = False
#     return did_write

# class WritableDisk:
#     def __enter__(self):
#         self.was_readonly = storage.getmount("/").readonly
#         if self.was_readonly:
#             storage.remount(
#                 "/", readonly=False, disable_concurrent_write_protection=True
#             )

#     def __exit__(self, exc_type, exc_value, exc_tb):
#         if self.was_readonly:
#             storage.remount(
#                 "/", readonly=True, disable_concurrent_write_protection=False
#             )
#         return False
