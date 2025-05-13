import array
import board
import audiobusio

def create_wav_header(sample_rate, bits_per_sample, num_samples):
    datasize = num_samples * bits_per_sample // 8
    header = bytearray(44)
    # RIFF header
    header[0:4] = b'RIFF'
    header[4:8] = (datasize + 36).to_bytes(4, 'little')  # File size - 8
    header[8:12] = b'WAVE'
    # Format chunk
    header[12:16] = b'fmt '
    header[16:20] = (16).to_bytes(4, 'little')  # Chunk size
    header[20:22] = (1).to_bytes(2, 'little')  # PCM format
    header[22:24] = (1).to_bytes(2, 'little')
    header[24:28] = (sample_rate).to_bytes(4, 'little')
    header[28:32] = (sample_rate * bits_per_sample // 8).to_bytes(4, 'little')  # Byte rate
    header[32:34] = (bits_per_sample // 8).to_bytes(2, 'little')  # Block align
    header[34:36] = (bits_per_sample).to_bytes(2, 'little')
    # Data chunk
    header[36:40] = b'data'
    header[40:44] = (datasize).to_bytes(4, 'little')
    return header

def create_wav(samples, sample_rate=16000, bits_per_sample=16):
    # Create header
    header = create_wav_header(sample_rate, bits_per_sample, len(samples))
    # Open file for writing
    # If samples are in array.array format, we need to convert to bytes
    sample_bytes = bytearray(len(samples) * 2)
    for i, sample in enumerate(samples):
        # Convert to 16-bit PCM (little-endian)
        sample_bytes[i*2] = sample & 0xFF
        sample_bytes[i*2 + 1] = (sample >> 8) & 0xFF
    return (header + sample_bytes)

def save_wav(filename, contents):
    with open(filename, 'wb') as f:
        f.write(contents)

class BadgeMic:
    def __init__(self):
        self.mic = audiobusio.PDMIn(board.GPIO41, board.GPIO42, sample_rate=16000, bit_depth=16, mono=True, startup_delay=0.01)
    def __del__(self):
        self.mic.deinit()
    def record(self, seconds):
        num_samples = int(seconds*16000)
        samples = array.array('H',[0]*num_samples)
        self.mic.record(samples, len(samples))
        return samples
    def wave(self, samples, filename=""):
        wav = create_wav(samples)
        if filename:
            save_wav(filename, wav)
        return wav
