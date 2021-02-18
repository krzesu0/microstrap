PY_FILES := $(shell find src/ -type f ! -name '.gitkeep')
COM := /dev/ttyUSB0
DEBUG := 0
MICROPYTHON_IAMGE := esp8266-20210202-v1.14.bin

init:
	mkdir -pv dest typings src

soft_flash:
	python soft_flash.py $(DEBUG) $(COM) $(PY_FILES)

hard_flash:
	python -m esptool --port $(COM) --baud 460800 erase_flash
	python -m esptool --port $(COM) --baud 460800 write_flash --flash_size=detect 0 $(MICROPYTHON_IAMGE)

download_from_flash:
	python download_flash.py $(DEBUG) $(COM)
