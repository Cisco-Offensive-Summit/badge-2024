__all__ = ["nvm_save", "nvm_open","nvm_free"]

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