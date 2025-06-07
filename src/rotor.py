# Original code from
# Gabe Emerson / Saveitforparts 2024, Email: gabe@saveitforparts.com

import socket
import RPi.GPIO as GPIO
import time
import threading

#initialize some variables
index = 0
az_last_time = 0

#listen to local port for rotctld commands
listen_ip = '0.0.0.0'  #listen on localhost
listen_port = 4533     #pass this from command line in future?

az_pulse = 0;
el_pulse = 0;
az = False # if true then move west, else east
el = False # if true then move up, else down
az_running = False
el_running = False
az_origin = False
el_origin = False

AZ_MIN = 90
AZ_MAX = 270
EL_MIN = 0
EL_MAX = 40

# define pinouts
ROTOR_AZ =        31
ROTOR_EL =        17
ROTOR_AZ_1 =      27
ROTOR_AZ_2 =      22
ROTOR_AZ_S =      18     # start/stop
ROTOR_EL_1 =      23
ROTOR_EL_2 =      24
ROTOR_EL_S =      25    # start/stop
ROTOR_AZ_ORIGIN = 30
ROTOR_EL_ORIGIN = 29

# Degree - ADC relation
EL_FACTOR = 5
AZ_FACTOR = 0.0615


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.cleanup()

GPIO.setup(ROTOR_AZ_S, GPIO.IN)
GPIO.setup(ROTOR_EL_S, GPIO.IN)

GPIO.setup(ROTOR_EL, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ROTOR_AZ, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ROTOR_AZ_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_AZ_2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_AZ_S, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_EL_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_EL_2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_EL_S, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ROTOR_AZ_ORIGIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ROTOR_EL_ORIGIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Helper functions
def azimuth_stop():
	GPIO.output(ROTOR_AZ_S, GPIO.HIGH)

def azimuth_start():
	GPIO.output(ROTOR_AZ_S, GPIO.LOW)

def elevation_stop():
	GPIO.output(ROTOR_EL_S, GPIO.HIGH)

def elevation_start():
	GPIO.output(ROTOR_EL_S, GPIO.LOW)

def rotator_stop():
	azimuth_stop()
	elevation_stop()

def rotor_up():
	global el
	el = True
	GPIO.output(ROTOR_EL_1, GPIO.HIGH)
	GPIO.output(ROTOR_EL_2, GPIO.HIGH)
	elevation_start()

def rotor_down():
	global el
	el = False
	GPIO.output(ROTOR_EL_1, GPIO.LOW)
	GPIO.output(ROTOR_EL_2, GPIO.LOW)
	elevation_start()

def rotor_east():
	global az
	az = False
	GPIO.output(ROTOR_AZ_1, GPIO.LOW)
	GPIO.output(ROTOR_AZ_2, GPIO.LOW)
	azimuth_start()

def rotor_west():
	global az
	az = True
	GPIO.output(ROTOR_AZ_1, GPIO.HIGH)
	GPIO.output(ROTOR_AZ_2, GPIO.HIGH)
	azimuth_start()

def count_az_pulse(channel):
	global az_pulse, az

	if az:
		az_pulse += 1
	elif az_pulse > 0:
		az_pulse -= 1

	if az_pulse < 0:
		az_pulse = 0



def count_el_pulse():
	global el_pulse, el

	if el:
		el_pulse += 1
	elif el_pulse > 0:
		el_pulse -= 1

def get_azimuth():
	global az_pulse
	return az_pulse * AZ_FACTOR + AZ_MIN;

def get_elevation():
	global el_pulse
	return el_pulse;

def az_stop(channel):
	global az_origin
	az_origin = True
	azimuth_stop()

def el_stop(channel):
	global el_origin
	el_origin = True
	elevation_stop()

def is_az_origin():
	global az_origin, az_pulse
	while True:
		az_origin = (GPIO.input(ROTOR_AZ_ORIGIN) == GPIO.HIGH)
		if az_origin:
			azimuth_stop()
			az_pulse = 0
			return

def is_el_origin():
	if GPIO.input(ROTOR_EL_ORIGIN):
		return True
	return False

def rotate_and_check():
	global az_running, el_running, target_az, el_target

	if az_running:
		az_diff = round(target_az - get_azimuth())
		if az_diff > 0:
			rotor_west()
		elif az_diff < 0:
			rotor_east()
		else:
			azimuth_stop()
			az_running = False

	#if el_running:
	#	el_diff = target_el - get_elevation()
	#	if el_diff > 0:
	#		rotor_up()
	#	elif el_diff < 0:
	#		rotor_down()
	#	else:
	#		elevation_stop()
	#		el_running = False

def handle_connection(conn):
	global current_az, current_el, target_az, target_el, az_running, el_running
	while True:
		try:
			data = conn.recv(100)  #get Gpredict's message
			if not data:
				break

			cmd = data.decode("utf-8").strip().split(" ")   #grab the incoming command

			#print("Received: ", cmd)    #debugging, what did Gpredict send?

			if cmd[0] == "p":   #Gpredict is requesting current position
				response = "{}\n{}\n".format(get_azimuth(), get_elevation())
				conn.send(response.encode('utf-8'))

			elif cmd[0] == "P":   #Gpredict is sending desired position
				target_az = float(cmd[1])
				target_el = float(cmd[2])
				if (target_az >= AZ_MIN) and (target_az <= AZ_MAX) and (target_el >= EL_MIN) and (target_el <= EL_MAX):
					print(f"Move antenna to: {target_az} {target_el}", end="\r")
					az_running = True
					el_running = True

				#Tell Gpredict things went correctly
				response="RPRT 0\n "  #Everything's under control, situation normal
				conn.send(response.encode('utf-8'))

			elif cmd[0] == "S":
				print('Gpredict disconnected')
				rotator_stop()
				break  # Beende den Thread

			rotate_and_check()

		except Exception as e:
			print(f"Error handling connection: {e}")
			rotator_stop()
			break  # Beende den Thread bei einem Fehler

	print("Connection handling thread exiting.")
	conn.close()  # Schließe die Verbindung im Thread

def start_server():
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
		server.bind((listen_ip, listen_port))
		server.listen()
		print(f"Listening on {listen_ip}:{listen_port}")
		while True:
			conn, addr = server.accept()
			print(f"Connected by {addr}")
			threading.Thread(target=handle_connection, args=(conn,), daemon=True).start()

# Main
if __name__ == "__main__":
	try:
#		while 1:
#			GPIO.output(ROTOR_AZ_1, GPIO.HIGH)
#			GPIO.output(ROTOR_AZ_2, GPIO.HIGH)
#			GPIO.output(ROTOR_AZ_S, GPIO.HIGH)

		GPIO.add_event_detect(ROTOR_AZ, GPIO.RISING, callback=count_az_pulse, bouncetime=25)

		threading.Thread(target=is_az_origin,  daemon=True).start()

		print(f"Move East")
		rotor_east()
		print(f"Move Rotor Down")
		rotor_down()
		print(f"AZ: {get_azimuth()}")
		print(f"EL: {get_elevation()} ")
		print("Ready")
		start_server()
	except KeyboardInterrupt:
		print("Shutting down.")
		rotator_stop()
		GPIO.cleanup()
