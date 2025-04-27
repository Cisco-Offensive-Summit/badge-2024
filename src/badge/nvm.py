__all__ = ["nvm_save", "nvm_open"]

import struct
import json

from binascii import a2b_base64 as base64Decode
from binascii import b2a_base64 as base64Encode
from badge.log import log
from microcontroller import nvm as board_NVM

###############################################################################

class MapSizeException(Exception): pass
class Base64WrapperException(Exception): pass
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
        current = self.head
        while current:
            if current is block:
                break
            current = current.next
        else:
            # Only happens if we never broke from the loop
            raise MemoryBlockListException("Cannot remove a block that is not in the list.")
    
        # Now it's safe to remove
        if block.prev:
            block.prev.next = block.next
        else:
            # Block was head
            self.head = block.next
    
        if block.next:
            block.next.prev = block.prev
        else:
            # Block was tail
            self.tail = block.prev
    
        # Clean up pointers (optional, but helps avoid accidental bugs)
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
                    current.stop = current.next.stop
                    self.remove(current.next)
                else:
                    current = current.next
            else:
                current = current.next

    def __iter__(self):
        current = self.head
        while current:
            yield current
            current = current.next

###############################################################################

class Base64Wrapper:
    def __init__(self, value=None, data=None, data_type=None):
        self._TYPE_BIT = 0
        self._TYPE_STR = 1
        self._TYPE_BOL = 2
        self._TYPE_INT = 3

        if data or data_type:
            if data or data_type:
                self.data = data
                self.data_type = data_type
            else:
                raise Base64WrapperException("data and data_type must both be non-None")
        elif data == None:
            self.data = bytearray()

        if value is not None:
            self.set(value)

    def set(self, value):
        """Serialize and store any basic Python type (or bytes) using base64."""
        try:
            if isinstance(value, (bytes, bytearray)):  # Directly handle byte data
                base64_data = base64Encode(value).decode("utf-8")
                self.data_type = self._TYPE_BIT
                self.size = len(base64_data)
            elif isinstance(value, str):  # Directly handle string type
                base64_data = base64Encode(value.encode("utf-8")).decode("utf-8")
                self.data_type = self._TYPE_STR
                self.size = len(base64_data)
            elif isinstance(value, bool):  # Handle boolean values
                base64_data = base64Encode(str(value).encode("utf-8")).decode("utf-8")
                self.data_type = self._TYPE_BOL
                self.size = len(base64_data)
            elif isinstance(value, int):  # Handle integer values by packing them
                base64_data = base64Encode(struct.pack("i", value)).decode("utf-8")
                self.data_type = self._TYPE_INT
                self.size = len(base64_data)
            else:
                raise ValueError("Unsupported type for base64 encoding")
            
            self.data = bytearray(base64_data, "utf-8")
        except Exception as e:
            raise ValueError(f"Error during base64 encoding: {e}")

    def get(self):
        """Deserialize and return the stored value."""
        try:
            base64_data = self.data.decode("utf-8")
            decoded_bytes = base64Decode(base64_data.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to deserialize: {e}")

        if self.data_type == self._TYPE_BOL:
            # If it was a boolean, decode it back as string and cast to bool
            if decoded_bytes == b"True" or decoded_bytes == b"False":
                return decoded_bytes.decode("utf-8") == "True"

        if self.data_type == self._TYPE_INT:
            # Try to decode as an integer (assumes it was packed with struct)
            try:
                number = struct.unpack("i", decoded_bytes)[0]
                return number
            except Exception as e:
                raise ValueError(f"Failed to unpack Int: {e}")

        if self.data_type == self._TYPE_BIT:
            return decoded_bytes

        if self.data_type == self._TYPE_STR:
            # Finally, decode back to a string
            return decoded_bytes.decode("utf-8")

        raise ValueError(f"Unrecognized data_type: {self.data_type}")

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        if not isinstance(value, bytearray):
            raise ValueError("value not of type: bytearray")

        self._data = value
        
    def __repr__(self):
        return f"<Base64Wrapper data={self.data}>"

    def __bytes__(self):
        return bytes(self.data)

###############################################################################

class _NVM:
    
    def __init__(self):
        self._NVM_SIZE = len(board_NVM)  # Ensure `board_NVM` is passed
        self._SIZE_START = 0
        self._SIZE_STRING_SIZE = 5
        self._SIZE_DATA_START = self._SIZE_START + self._SIZE_STRING_SIZE
        self._SIZE_DATA_SIZE = 4
        self._DATA_START = self._NVM_SIZE // 10  # 10% of NVM size
        self._MAP_START = 9  # Starting index for the map
        self._MAX_MAP_SIZE = self._DATA_START - self._MAP_START  # Max map size should be positive
        self._MAX_DATA_SIZE = self._NVM_SIZE - self._DATA_START  # Remaining space for data

        # Ensure that the calculated sizes are valid
        if self._MAX_MAP_SIZE < 0:
            raise ValueError("Map size calculation resulted in a negative value. Check your NVM layout.")

        self._read_in_map()

    def _get_map_size(self):
        # Get the first 5 bytes from the NVM (to check for the string 'size:')
        data = board_NVM[0:5]
        
        # Decode the first 5 bytes to string
        s = data.decode("utf-8")
        
        # Check if the string matches 'size:'
        if s == 'size:':
            # Extract the next 4 bytes (bytes 5, 6, 7, and 8) for the integer size
            data = board_NVM[5:9]  # slicing 5 to 9 includes byte 8
            size = struct.unpack("I", data)[0]  # Unpack as unsigned int (I)
            return size
        else:
            # Return 0 if 'size:' is not found
            return 0

    def _read_in_map(self):
        # Get the map size
        map_size = self._get_map_size()

        if map_size == 0: #No map needs to create one:
            self.map = {}
            log("MAP_SIZE = 0: Creating blank map")
            self._build_list()
            return

        if map_size > self._MAX_MAP_SIZE:
            log("Recorded map size too large. Setting to Max")
            map_size = self._MAX_MAP_SIZE
        # Read the data from NVM based on the map size
        data = board_NVM[self._MAP_START:self._MAP_START + map_size]
        
        # Decode the byte data to a UTF-8 string
        decoded_data = data.decode("utf-8")
        
        try:
            # Load the decoded string into a JSON object
            self._map = json.loads(decoded_data)
        except ValueError as e:
            # Handle invalid JSON format
            log(f"Error decoding JSON: {e}")
            log(f"Map Corruption: RESETTING")
            self.map = {}
        except Exception as e:
            # Handle any other errors that may occur
            log(f"Unexpected error while reading map: {e}")
            log(f"Map Corruption: RESETTING")
            self.map = {}

        self._build_list()

    def _print_map(self, map):
        return json.dumps(map)

    def _build_list(self):
        global _mbl

        mb = _MemoryBlock(self._DATA_START, self._DATA_START + self._MAX_DATA_SIZE, 0)
        _mbl = _MemoryBlockList(mb)

        # Check if the map is loaded
        if not self.map:
            log("No map to build from.")
            return        

        log(self._print_map(self.map))
        # Iterate over the map and create memory blocks for each item
        for key, value in self.map.items():
            new_block = _MemoryBlock(value[0],value[1], self._USED)
            
            # Add this new block to the memory block list
            if self._mbl is None:
                self._mbl = new_block  # First block becomes the head
            else:
                # Traverse to the end and append
                current = self._mbl
                while current.next is not None:
                    current = current.next
                current.next = new_block  # Append new block at the end
        
        log(f"Built memory block list: {self._mbl}")

    def _set_size(self, size: int) -> None:
        """Set the map size and handle associated state updates."""
        self._map_size = size
        data = bytearray("size:", "utf-8")
        board_NVM[self._SIZE_START:self._SIZE_START+self._SIZE_STRING_SIZE] = data
        data = bytearray(struct.pack("I", size))
        board_NVM[self._SIZE_DATA_START:self._SIZE_DATA_START + self._SIZE_DATA_SIZE] = data

        if size == 0:
            print("Warning: The map is empty.")
        # You could also add additional logging, checks, or actions here

    def save_data(self, name: str, base64_data: Base64Wrapper):
        """Save data to the NVM and update the map and memory block list."""

        map = self.map
        # If that save file is already in the list see if we can save it in the same place first
        # If it is the same size, write directly over it.
        # If it is smaller keep the same start and change the stop.
        # We then need to create a new FREE block for the remaining space
        # If it is larger find it a new space.
        # Remove the old space first incase you need to compact for the new one
        # Last write the new data to its new home.
        if name in map:
            old_meta = [map[name][0], map[name][1]]
            size = old_meta[1] - old_meta[0]
            if size >= base64_data.size:
                # Save and record new entry
                board_NVM[map[name][0]:map[name][0]+base64_data.size] = base64_data.data
                map[name][1] = map[name][0]+base64_data.size
                map[name][2] = base64_data.data_type
                # If it was larger then create the free block
                if size > base64_data.size:
                    _mbl.insert(_MemoryBlock(map[name][1],old_meta[1],0))

                self.map = map
                return
            # Else it needs a new spot and its old spot freed
            else:
                for block in _mbl:
                    if block.start == old_meta[0] and block.stop == old_meta[1]:
                        del map[name]
                        _mbl.free(block)
                        break

        start_end = self._find_new_space(base64_data.size)  # Find space for data.
        if start_end is None:
            raise ValueError("Not enough save space in memory blocks.")

        start, end = start_end

        # Store data in NVM
        board_NVM[slice(*start_end)] = base64_data.data

        # Update memory block list to mark the block as used
        current = _mbl.head
        while current:
            if current.start == start and current.stop >= end:
                # We found the block and now we mark it as used
                current.block_type = current._USED

                # If the block is larger than the data, we might need to split it.
                if current.stop > end:
                    new_block = _MemoryBlock(end, current.stop, current._FREE)
                    _mbl.insert(new_block)  # Insert the remaining free block after the used block
                    current.stop = end  # Adjust the used block's stop to fit the saved data
                break
            current = current.next

        # Update the memory map with the new data.
        log(f"data_type before saving {base64_data.data_type}")
        map[name] = list(start_end) + [base64_data.data_type]
        self.map = map

    def read_data(self, name:str):
        metadata = self.map[name]
        if not isinstance(metadata, list):
            raise ValueError("metadata not of type \"list\"")
        return board_NVM[metadata[0]:metadata[1]], metadata[2]

    def _find_new_space(self, length: int):
        """Find an available block of memory that can fit the data."""
        def search():
            current = _mbl.head
            while current:
                if current.block_type == current._FREE and current.size() >= length:
                    return (current.start, current.start + length)
                current = current.next
            return None

        # First attempt to find space
        result = search()
        if result:
            return result

        # If no space found, compact memory and try again
        self._compact_memory()
        result = search()
        if result:
            return result

        # If still no space, raise
        raise MemoryBlockListException("Not enough space in memory to store data.")
        
    def free_data(self, name: str):
        """Free the data associated with the given name and update the memory block list."""
        map_copy = self.map
        log(self._print_map(map_copy))


        try:
            start, end, data_type = map_copy[name]
        except KeyError:
            raise ValueError(f"Data with name '{name}' not found in map.")
        
        # Mark the corresponding memory block as free
        current = _mbl.head
        while current:
            if current.start == start and current.stop == end:
                current.block_type = current._FREE
                _mbl._clean()
                break
            current = current.next

        # Remove from map and reassign to trigger the setter
        del map_copy[name]
        self.map = map_copy

        log(f"Data with name '{name}' has been freed and removed from map.")

    def _compact_memory(self):
        """Compacts memory by moving used blocks down and merging free space."""
        log("Starting memory compaction...")

        map_copy = self.map
        current = _mbl.head

        new_position = 0  # Where the next used block should go

        while current:
            block_size = current.stop - current.start

            if current.block_type == current._USED:
                if current.start != new_position:
                    log(f"Moving block from {current.start}-{current.stop} to {new_position}-{new_position + block_size}")
                    # Physically move the data
                    board_NVM[new_position:new_position + block_size] = board_NVM[current.start:current.stop]
                    
                    # Update map to reflect new position
                    for name, (start, end, data_type) in map_copy.items():
                        if start == current.start and end == current.stop:
                            map_copy[name] = (new_position, new_position + block_size, data_type)
                            break

                    # Update the memory block itself
                    current.start = new_position
                    current.stop = new_position + block_size

                # Advance new_position
                new_position += block_size

            current = current.next

        # After moving all used blocks, fix the free block
        if new_position < self._MAP_START:
            # There should be exactly one free block now
            free_block = _mbl.head
            while free_block.next:
                free_block = free_block.next
            
            free_block.start = new_position
            free_block.stop = self._MAP_START
            free_block.block_type = free_block._FREE
            free_block.next = None

        self.map = map_copy  # Trigger setter to update map storage

        log("Memory compaction completed.")

    @property
    def map(self):
        """Getter for the map."""
        return self._map

    @map.setter
    def map(self, new_map):
        """Setter for the map that also updates the size."""
        if not isinstance(new_map, dict):
            raise ValueError("The map must be a dictionary.")

        json_data = json.dumps(new_map)
        data = bytearray(json_data, "utf-8")
        map_size = len(data)

        if map_size > self._MAX_MAP_SIZE:
            raise MapSizeException("Map size too large" +f"size: {map_size}, allowed: {self._MAX_MAP_SIZE}")

        self._map = new_map
        log(self._print_map(self._map))

        board_NVM[self._MAP_START:self._MAP_START + map_size] = data
        # Update the map size based on the new map
        self._set_size(map_size)  # Assuming size is the length of the map


_mbl = _MemoryBlockList()
_nvm = _NVM()

###############################################################################

# Save data with memory block list integration
def nvm_save(name: str, data):
    """Save data to NVM, interacting with the memory block list."""
    encoded_data = Base64Wrapper(data)
    _nvm.save_data(name, encoded_data)


# Open and return data from NVM
def nvm_open(name: str):
    """Open data from NVM, using the memory block list."""
    b64_data, data_type = _nvm.read_data(name)
    decoded_data = Base64Wrapper(data=b64_data, data_type=data_type)
    return decoded_data.get()

# Delete saved data
def nvm_free(name: str):
    """Deletes the map entry and allocates as free space"""
    _nvm.free_data(name)