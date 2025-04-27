from badge.log import log

###############################################################################

class MemoryBlockException(Exception): pass
class MemoryBlockListException(Exception): pass

###############################################################################

class _MemoryBlock:
    def __init__(self, start:int, stop:int, block_type:int):
        self._FREE = 0
        self._USED = 1

        self.start = start
        self.stop = stop
        self.block_type = block_type

        self.prev = None  # Previous block
        self.next = None  # Next block


    @property
    def start(self) -> int:
        return self._start

    @start.setter
    def start(self, value) -> None:
        if value > 0:
            self._start = value
        else:
            raise MemoryBlockException("start value must be a positive int.")

    @property
    def stop(self) -> int:
        return self._stop

    @stop.setter
    def stop(self, value):
        if value > self._start:
            self._stop = value
        else:
            raise MemoryBlockException("stop value must be greater then start.")

    def size(self) -> int:
        return self._stop - self._start

    def print(self):
        log(f'<SELF[{id(self)}] : start[{self.start}] : stop[{self.stop}] : data_type[{self.block_type}], NEXT[{id(self.next)}] : PREV[{id(self.prev)}]>')

    @property
    def block_type(self) -> int:
        return self._block_type

    @block_type.setter
    def block_type(self, value) -> None:
        if (value == self._FREE) or (value == self._USED):
            self._block_type = value
        else:
            raise MemoryBlockException("block_type must be either a 0 or 1")

    def __lt__(self, other):
        if not isinstance(other, _MemoryBlock):
            return NotImplemented
        return self.stop <= other.start

    def __eq__(self, other):
        if not isinstance(other, _MemoryBlock):
            return NotImplemented
        return self.start == other.start and self.stop == other.stop and self.block_type == other.block_type

    def __gt__(self, other):
        if not isinstance(other, _MemoryBlock):
            return NotImplemented
        return self.start <= other.stop

###############################################################################

class _MemoryBlockList:
    def __init__(self, new_block: _MemoryBlock = None):
        self.head = None
        self.tail = None
        if new_block:
            self.insert(new_block)

    def insert(self, new_block: _MemoryBlock):
        if self.head is None:
            self.head = self.tail = new_block
            return

        current = self.head
        while current is not None and new_block.start > current.start:
            current = current.next

        if current is not None and current == new_block:
            return  # Duplicate MemoryBlock, ignore.
        if current is not None and current.start == new_block.start:
            raise MemoryBlockListException("Block with duplicate start address but different end or type.")

        if current is None:
            self.tail.next = new_block
            new_block.prev = self.tail
            self.tail = new_block
        elif current is self.head:
            new_block.next = self.head
            self.head.prev = new_block
            self.head = new_block
        else:
            prev_block = current.prev
            prev_block.next = new_block
            new_block.prev = prev_block
            new_block.next = current
            current.prev = new_block

    def remove(self, block: _MemoryBlock):
        """Remove a block from the list."""
        # Sanity check: is block in the list?
        log(f"Looking for block: ", id(block))
        current = self.head

        while current:
            log("Looking at block:", id(current))
            if current == block:
                log("Found it")
                break
            current = current.next
        else:
            # Only happens if we never broke from the loop
            raise MemoryBlockListException("Cannot remove a block that is not in the list.")
        log("Made it here")
        block.print()
        # Now it's safe to remove
        if block.prev:
            log("<PREV>")
            block.prev.print()
            block.prev.next = block.next
            log("<PREV_AFTER>")
            block.prev.print()
        else:
            log("<BLOCK_WAS HEAD>")
            # Block was head
            self.head = block.next
        if block.next:
            log("<NEXT>")
            block.next.print()
            block.next.prev = block.prev
            log("<NEXT_AFTER>")
            block.next.print()
        else:
            # Block was tail
            log("<BLOCK_WAS TAIL>")
            self.tail = block.prev
        # Clean up pointers
        block.prev = None
        block.next = None
        return block

    def pop(self):
        if self.tail is not None:
            self.remove(self.tail)
        else:
            raise MemoryBlockListException("Cannot pop from an empty list.")

    def free(self, block:_MemoryBlock):
        if block.block_type != block._USED:
            raise MemoryBlockListException("block already free")
        block.block_type = block._FREE
        self._clean()

    def _clean(self):
        current = self.head
        
        while current is not None:
            if current.next:
                if current.block_type == 0 and current.next.block_type == 0:
                    log("About to remove block:", id(current.next))
                    to_remove = current.next
                    current.stop = to_remove.stop
                    self.remove(to_remove)
                else:
                    current = current.next
            else:
                current = current.next

    def __iter__(self):
        current = self.head
        while current:
            yield current
            current = current.next

_mbl = _MemoryBlockList()
