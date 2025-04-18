# initfs

This folder contains the default testing files that will be flashed to the badge
on filesystem initialization.

To reset the filesystem you can use:

```python
from storage import erase_filesystem
erase_filesystem()
```
