.DEFAULT_GOAL := all

all:
	@scp -pr * pi@192.168.150.229:/home/pi/sat_rotor
