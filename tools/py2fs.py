import sys, pathlib

filesystem_str_start = """
/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2017 Scott Shawcroft for Adafruit Industries
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "supervisor/filesystem.h"

#include "extmod/vfs_fat.h"
#include "lib/oofatfs/ff.h"
#include "lib/oofatfs/diskio.h"

#include "py/mpstate.h"

#include "supervisor/flash.h"
#include "supervisor/linker.h"

static mp_vfs_mount_t _mp_vfs;
static fs_user_mount_t _internal_vfs;

static volatile uint32_t filesystem_flush_interval_ms = CIRCUITPY_FILESYSTEM_FLUSH_INTERVAL_MS;
volatile bool filesystem_flush_requested = false;

void filesystem_background(void) {
    if (filesystem_flush_requested) {
        filesystem_flush_interval_ms = CIRCUITPY_FILESYSTEM_FLUSH_INTERVAL_MS;
        // Flush but keep caches
        supervisor_flash_flush();
        filesystem_flush_requested = false;
    }
}

inline void filesystem_tick(void) {
    if (filesystem_flush_interval_ms == 0) {
        // 0 means not turned on.
        return;
    }
    if (filesystem_flush_interval_ms == 1) {
        filesystem_flush_requested = true;
        filesystem_flush_interval_ms = CIRCUITPY_FILESYSTEM_FLUSH_INTERVAL_MS;
    } else {
        filesystem_flush_interval_ms--;
    }
}


static void make_empty_file(FATFS *fatfs, const char *path) {
    FIL fp;
    f_open(fatfs, &fp, path, FA_WRITE | FA_CREATE_ALWAYS);
    f_close(&fp);
}

/*
static void make_sample_code_file(FATFS *fatfs) {
    #if CIRCUITPY_FULL_BUILD
    FIL fs;
    UINT char_written = 0;
    const byte buffer[] = "print(\"Hello World!\")\n";
    // Create or modify existing code.py file
    f_open(fatfs, &fs, "/code.py", FA_WRITE | FA_CREATE_ALWAYS);
    f_write(&fs, buffer, sizeof(buffer) - 1, &char_written);
    f_close(&fs);
    #else
    make_empty_file(fatfs, "/code.py");
    #endif
}
*/

// Offsummit add file
static void make_file_with_contents(FATFS *fatfs, const char *filename, const byte *content, UINT size) {
    FIL fs;
    // Create or modify existing code.py file
    f_open(fatfs, &fs, filename, FA_WRITE | FA_CREATE_ALWAYS);
    f_write(&fs, content, size, &size);
    f_close(&fs);
}

"""

filesystem_str_post_func = """
// we don't make this function static because it needs a lot of stack and we
// want it to be executed without using stack within main() function
bool filesystem_init(bool create_allowed, bool force_create) {
    // init the vfs object
    fs_user_mount_t *vfs_fat = &_internal_vfs;
    vfs_fat->blockdev.flags = 0;
    supervisor_flash_init_vfs(vfs_fat);

    mp_vfs_mount_t *vfs = &_mp_vfs;
    vfs->len = 0;

    // try to mount the flash
    FRESULT res = f_mount(&vfs_fat->fatfs);
    if ((res == FR_NO_FILESYSTEM && create_allowed) || force_create) {
        // No filesystem so create a fresh one, or reformat has been requested.
        uint8_t working_buf[FF_MAX_SS];
        BYTE formats = FM_FAT;
        #if FF_FS_EXFAT
        formats |= FM_EXFAT | FM_FAT32;
        #endif
        res = f_mkfs(&vfs_fat->fatfs, formats, 0, working_buf, sizeof(working_buf));
        if (res != FR_OK) {
            return false;
        }
        // Flush the new file system to make sure it's repaired immediately.
        supervisor_flash_flush();

        // set label
        #ifdef CIRCUITPY_DRIVE_LABEL
        res = f_setlabel(&vfs_fat->fatfs, CIRCUITPY_DRIVE_LABEL);
        #else
        res = f_setlabel(&vfs_fat->fatfs, "CIRCUITPY");
        #endif
        if (res != FR_OK) {
            return false;
        }

        // inhibit file indexing on MacOS
        res = f_mkdir(&vfs_fat->fatfs, "/.fseventsd");
        if (res != FR_OK) {
            return false;
        }
        make_empty_file(&vfs_fat->fatfs, "/.metadata_never_index");
        make_empty_file(&vfs_fat->fatfs, "/.Trashes");
        make_empty_file(&vfs_fat->fatfs, "/.fseventsd/no_log");
        #if CIRCUITPY_OS_GETENV
        make_empty_file(&vfs_fat->fatfs, "/settings.toml");
        #endif
        // make a sample code.py file
        //make_sample_code_file(&vfs_fat->fatfs);

"""

filesystem_str_post_dir = """
        // create empty lib directory
        //res = f_mkdir(&vfs_fat->fatfs, "/lib");
        //if (res != FR_OK) {
        //    return false;
        //}

"""

filesystem_str_final = """

        // and ensure everything is flushed
        supervisor_flash_flush();
    } else if (res != FR_OK) {
        return false;
    }

    vfs->str = "/";
    vfs->len = 1;
    vfs->obj = MP_OBJ_FROM_PTR(vfs_fat);
    vfs->next = NULL;

    MP_STATE_VM(vfs_mount_table) = vfs;

    // The current directory is used as the boot up directory.
    // It is set to the internal flash filesystem by default.
    MP_STATE_PORT(vfs_cur) = vfs;

    #if CIRCUITPY_STORAGE_EXTEND
    supervisor_flash_update_extended();
    #endif

    return true;
}

void PLACE_IN_ITCM(filesystem_flush)(void) {
    // Reset interval before next flush.
    filesystem_flush_interval_ms = CIRCUITPY_FILESYSTEM_FLUSH_INTERVAL_MS;
    supervisor_flash_flush();
    // Don't keep caches because this is called when starting or stopping the VM.
    supervisor_flash_release_cache();
}

void filesystem_set_internal_writable_by_usb(bool writable) {
    fs_user_mount_t *vfs = &_internal_vfs;

    filesystem_set_writable_by_usb(vfs, writable);
}

void filesystem_set_writable_by_usb(fs_user_mount_t *vfs, bool usb_writable) {
    if (usb_writable) {
        vfs->blockdev.flags |= MP_BLOCKDEV_FLAG_USB_WRITABLE;
    } else {
        vfs->blockdev.flags &= ~MP_BLOCKDEV_FLAG_USB_WRITABLE;
    }
}

bool filesystem_is_writable_by_python(fs_user_mount_t *vfs) {
    return (vfs->blockdev.flags & MP_BLOCKDEV_FLAG_CONCURRENT_WRITE_PROTECTED) == 0 ||
           (vfs->blockdev.flags & MP_BLOCKDEV_FLAG_USB_WRITABLE) == 0;
}

bool filesystem_is_writable_by_usb(fs_user_mount_t *vfs) {
    return (vfs->blockdev.flags & MP_BLOCKDEV_FLAG_CONCURRENT_WRITE_PROTECTED) == 0 ||
           (vfs->blockdev.flags & MP_BLOCKDEV_FLAG_USB_WRITABLE) != 0;
}

void filesystem_set_internal_concurrent_write_protection(bool concurrent_write_protection) {
    filesystem_set_concurrent_write_protection(&_internal_vfs, concurrent_write_protection);
}

void filesystem_set_concurrent_write_protection(fs_user_mount_t *vfs, bool concurrent_write_protection) {
    if (concurrent_write_protection) {
        vfs->blockdev.flags |= MP_BLOCKDEV_FLAG_CONCURRENT_WRITE_PROTECTED;
    } else {
        vfs->blockdev.flags &= ~MP_BLOCKDEV_FLAG_CONCURRENT_WRITE_PROTECTED;
    }
}

bool filesystem_present(void) {
    return _mp_vfs.len > 0;
}

FATFS *filesystem_circuitpy(void) {
    if (!filesystem_present()) {
        return NULL;
    }
    return &_internal_vfs.fatfs;
}
"""

def get_file_as_bytes(s: str) -> str:
    ret = "\tconst unsigned char file[] = {\n"
    with open(s, 'rb') as f:
        file_bytes = f.read()

        count = 0
        for i in range(len(file_bytes)):
            if count == 0:
                ret += '\t\t'

            if i == len(file_bytes)-1:
                ret += "0x{:02x}".format(file_bytes[i])
            else:
                ret += "0x{:02x}, ".format(file_bytes[i])
            count += 1

            if count == 25 and i != len(file_bytes)-1:
                ret += '\n'
                count = 0
    
    ret += "\n\t};"

    return ret

def get_func_for_file(p: str, lp: str) -> str:
    file_bytes_str = get_file_as_bytes(p)
    try:
        friendly_name = p.rsplit('.', 1)[0].rsplit('/', 1)[1]
    except IndexError:
        friendly_name = p.rsplit('.', 1)[0]
    #ending = p.rsplit('.', 1)[1]

    func = "static void offsummit_make_{}(FATFS *fatfs)".format(friendly_name)
    func += " {\n"
    func += file_bytes_str
    func += '\n\n'
    func += f'\tmake_file_with_contents(fatfs, "{lp}", file, sizeof(file));\n'
    func += "}\n\n"

    return [func, f"offsummit_make_{friendly_name}(&vfs_fat->fatfs);"]

def get_call_for_dir(p: str):
    ret = f'\t\tres = f_mkdir(&vfs_fat->fatfs, "{p}");\n'
    ret += '\t\tif (res != FR_OK) {\n'
    ret += '\t\t\treturn false;\n'
    ret += '\t\t}\n\n'
    return ret    

def usage():
    print("py2fs.py DIRECTORY_TO_FS")
    exit(1)

def main(path: str):
    if path[-1] == '/':
        path = path[:-1]

    p = pathlib.Path(path).rglob('*')
    files = [str(x) for x in p if x.is_file()]
    p = pathlib.Path(path).rglob('*')
    dirs = [str(x).removeprefix(path) for x in p if x.is_dir()]
    
    file_acc = []
    for file in files:
        if file.removeprefix(path) == "/README.md":
            continue
        elif file.rsplit('/', 1)[-1].startswith('_'):
            continue
        file_acc.append(get_func_for_file(file, file.removeprefix(path)))

    dirs_acc = []
    for d in dirs:
        dirs_acc.append(get_call_for_dir(d))

    fs_acc = filesystem_str_start
    for f in file_acc:
        fs_acc += f[0]
    fs_acc += filesystem_str_post_func
    for d in dirs_acc:
        fs_acc += d
    fs_acc += filesystem_str_post_dir
    for f in file_acc:
        fs_acc += f"\t\t{f[1]}\n"
    fs_acc += filesystem_str_final
    
    print(fs_acc)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    
    main(sys.argv[1])