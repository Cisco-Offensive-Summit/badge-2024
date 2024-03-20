# Firmware initial write

This is where files we want installed on the badge by default should be kept.
Note: These should mostly be copies of what lives in `/src`


## How to change firmware init files

1. Put file structure you want here:
    - EX:
    ```
    boot.py
    code.py
    lib/
        lib.mpy
        otherlib.mpy
    bmps/
        epd_logo.bmp
    ```
    - And file that starts with an '_' is ignored
2. Use the tool `py2fs.py` to create a `filesystem.c` file.
    - EX: `python3 tools/py2fs.py firmware/init_files/ > filesystem.c`
3. Copy the created filesystem.c to `circuitpython/supervisor/shared/filesystem.c`
4. Compile firmware with instructions in above directory
5. Hope you dont get memory errors 😅
    - See MPY section if you do

## Reset badge

Factory reset code:
```python
import storage
storage.erase_filesystem()
```

## MPY

Some files are too large to write on firmware init, so they must be compiled to mpy files.  
This file limit seems to be somewhere around 8000 bytes, probably due to some stack alloc limits.

More info here: https://docs.micropython.org/en/latest/reference/mpyfiles.html

Generally mpy files are faster to run and smaller, but badge owners cant read them easily.  
Actually could be a cool way to program in easter eggs.