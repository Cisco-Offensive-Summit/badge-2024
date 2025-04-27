import struct

from binascii import a2b_base64 as base64Decode
from binascii import b2a_base64 as base64Encode
from badge.log import log

###############################################################################

class Base64WrapperException(Exception): pass

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

