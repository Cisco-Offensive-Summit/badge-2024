# Generic Implementation of an app that others should follow
from pdepd import EPD
from adafruit_st7735r import ST7735R

class App:
    # Init
    def __init__(self, lcd: ST7735R, epd: EPD) -> App:
        self.lcd = lcd
        self.epd = epd
    
    # Destructor
    def __del__(self) -> None:
        pass

    # Setup
    def setup(self) -> bool:
        raise NotImplementedError

    # Run
    def run(self) -> bool:
        raise NotImplementedError