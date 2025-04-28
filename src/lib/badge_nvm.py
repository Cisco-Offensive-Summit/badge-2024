__all__ = ["nvm_save", "nvm_open","nvm_free","nvm_compact","nvm_info","nvm_format()","nvm_wipe"]

import struct
import json

from memory_block import MemoryBlockListException
from memory_block import _mbl
from memory_block import _MemoryBlock
from memory_block import _MemoryBlockList
from Base64Wrapper import Base64Wrapper
from badge.log import log
from microcontroller import nvm as board_NVM

###############################################################################

class MapSizeException(Exception): pass

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
            log("_read_in_map:> MAP_SIZE = 0: Creating blank map")
            self._build_list()
            return

        if map_size > self._MAX_MAP_SIZE:
            log("_read_in_map:> Recorded map size too large. Setting to Max")
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
            log(f"_read_in_map:> Error decoding JSON: {e}")
            log(f"_read_in_map:> Map Corruption: RESETTING")
            self.map = {}
        except Exception as e:
            # Handle any other errors that may occur
            log(f"_read_in_map:> Unexpected error while reading map: {e}")
            log(f"_read_in_map:> Map Corruption: RESETTING")
            self.map = {}

        self._build_list()

    def _print_map(self, map):
        return json.dumps(map)

    def _build_list(self):
        global _mbl
        MAX = self._NVM_SIZE
        MIN = self._DATA_START
        # Check if the map is loaded
        if not self.map:
            mb = _MemoryBlock(self._DATA_START, self._DATA_START + self._MAX_DATA_SIZE, 0)
            _mbl = _MemoryBlockList(mb)
            log("_build_list:> No map to build from.")
            return        

        # Iterate over the map and create memory blocks for each item
        for key, value in self.map.items():
            new_block = _MemoryBlock(value[0],value[1], 1)
            _mbl.insert(new_block)

        for block in _mbl:
            if block.block_type == 1:
                log("_build_list:> start of loop")
                start = block.start
                stop = block.stop
                # If this is the first in the list and it isn't a FREE block 
                # Create a free block and inster it into the list.
                log(f"_build_list:> block.prev {block.prev} | start {start} | stop {stop} | block_type {block.block_type}")
                if block.prev is None and start is not MIN:
                    log(f'_build_list:> creating START block from {MIN} to {start}')
                    mb = _MemoryBlock(MIN, start, 0)
                    _mbl.insert(mb)

                # It's the last in the list and all the memory isn't accounted for
                # Create a free block with the size difference between MAX and block.stop
                log(f"_build_list:> block.next {block.next}")
                if block.next is None and stop < MAX:
                    log(f'_build_list:> creating END block from {MAX} to {stop}')
                    mb = _MemoryBlock(stop, MAX, 0)
                    _mbl.insert(mb)

                # There is a node behind me. Check if its stop point is less the my start
                # If it is then create a free block and insert it into the list.
                log(f"_build_list:> block.prev {block.prev}")
                if block.prev:
                    prev_stop = block.prev.stop
                    if prev_stop < start:
                        log(f'_build_list:> creating free block from {prev_stop} to {start}')
                        mb = _MemoryBlock(prev_stop, start, 0)
                        _mbl.insert(mb)
        log("_build_list")
        self.print_memory_block_details()

    def print_memory_block_details(self):
        current = _mbl.head
        if not current:
            print("Memory block list is empty.")
            return
        
        print("Memory Block List:")
        node_index = 1
        while current:
            block_type = "FREE" if current.block_type == 0 else "USED"
            print(f"Node {node_index}:")
            print(f"  Start: {current.start}")
            print(f"  Stop: {current.stop}")
            print(f"  Block Type: {block_type} (Type Code: {current.block_type})")
            print(f"  Next Node: {current.next if current.next else 'None'}")
            print("-" * 30)  # separator between nodes
            current = current.next
            node_index += 1
        print("End of Memory Block List.")

    def _set_size(self, size: int) -> None:
        """Set the map size and handle associated state updates."""
        self._map_size = size
        data = bytearray("size:", "utf-8")
        board_NVM[self._SIZE_START:self._SIZE_START+self._SIZE_STRING_SIZE] = data
        data = bytearray(struct.pack("I", size))
        board_NVM[self._SIZE_DATA_START:self._SIZE_DATA_START + self._SIZE_DATA_SIZE] = data

        if size == 0:
            log("_set_size:> Warning: The map is empty.")

    def erase_all(self) -> None:
        """Sets the index map size to 0 so a new map will be drawn next read."""
        data = bytearray("size:", "utf-8")
        board_NVM[self._SIZE_START:self._SIZE_START+self._SIZE_STRING_SIZE] = data
        data = bytearray(struct.pack("I", 0))
        board_NVM[self._SIZE_DATA_START:self._SIZE_DATA_START + self._SIZE_DATA_SIZE] = data

    def save_data(self, name: str, base64_data: Base64Wrapper):
        """Save data to the NVM and update the map and memory block list."""
        log("save_data")
        self.print_memory_block_details()
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
        map[name] = list(start_end) + [base64_data.data_type]
        self.map = map

    def read_data(self, name:str):
        if name not in self.map:
            raise ValueError(f"No entry found for '{name}' in map.")
        metadata = self.map[name]
        if not isinstance(metadata, list):
            raise ValueError("metadata not of type \"list\"")
        return board_NVM[metadata[0]:metadata[1]], metadata[2]

    def _find_new_space(self, length: int):
        """Find an available block of memory that can fit the data."""
        log("_find_new_spaces")
        self.print_memory_block_details()
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
        self.compact_memory()
        result = search()
        if result:
            return result

        # If still no space, raise
        raise MemoryBlockListException("Not enough space in memory to store data.")
        
    def free_data(self, name: str):
        """Free the data associated with the given name and update the memory block list."""
        log("free_data")
        self.print_memory_block_details()
        map_copy = self.map

        if name not in map_copy:
            log(f"free_data:> Data with name '{name}' not found in map.")
            return

        start, end, data_type = map_copy[name]
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

        log(f"free_data:> Data with name '{name}' has been freed and removed from map.")

    def compact_memory(self):
        """Compacts memory by moving used blocks down and merging free space."""
        log("compact_memory:> Starting memory compaction...")

        map_copy = self.map
        current = _mbl.head

        new_position = self._DATA_START # Where the next used block should go

        while current:
            block_size = current.stop - current.start

            if current.block_type == current._USED:
                if current.start != new_position:
                    log(f"compact_memory:> Moving block from {current.start}-{current.stop} to {new_position}-{new_position + block_size}")
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

        log("compact_memory:> Memory compaction completed.")

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

        board_NVM[self._MAP_START:self._MAP_START + map_size] = data
        # Update the map size based on the new map
        self._set_size(map_size) 

_nvm = _NVM()

###############################################################################

# Save data with memory block list integration
def nvm_save(name: str, data):
    """Save data to NVM, interacting with the memory block list."""
    encoded_data = Base64Wrapper(data)
    _nvm.save_data(name, encoded_data)


# Open and return data from NVM
def nvm_open(name: str):
    try:
        """Open data from NVM, using the memory block list."""
        b64_data, data_type = _nvm.read_data(name)
    except ValueError:
        raise

    decoded_data = Base64Wrapper(data=b64_data, data_type=data_type)
    return decoded_data.get()

# Delete saved data
def nvm_free(name: str):
    """Deletes the map entry and allocates as free space"""
    _nvm.free_data(name)

def nvm_compact():
    """Trigger memory compaction to consolidate free space in NVM."""
    _nvm.compact_memory()

def nvm_info():
    """Print a summary of all saved entries in NVM, showing their ranges and data types."""
    print("NVM Map:")
    for name, (start, stop, dtype) in _nvm.map.items():
        print(f"- {name}: {start}-{stop} ({dtype})")

def nvm_format():
    """Erase the entire NVM, clearing all saved data and resetting the map."""
    _nvm.erase_all()

def nvm_wipe():
    """Delete each individual item in the NVM map one by one."""
    for name in list(_nvm.map.keys()):
        _nvm.free_data(name)

def print_list():
    current = _mbl.head
    while current:
        print(f"[{current.start}-{current.stop}] ({'FREE' if current.block_type == 0 else 'USED'} ({current.block_type}))", end=" -> ")
        current = current.next
    print("None")

def print_memory_block_details():
    _nvm.print_memory_block_details()