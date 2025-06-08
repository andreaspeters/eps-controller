# Original code from
# Gabe Emerson / Saveitforparts 2024, Email: gabe@saveitforparts.com

import socket
import time
import threading
import serial
import regex as re


#listen to local port for rotctld commands
listen_ip = '0.0.0.0'  #listen on localhost
listen_port = 4533     #pass this from command line in future?
serial_port = '/dev/ttyUSB2'

def handle_connection(conn):
	while True:
		try:
			data = conn.recv(100)  #get Gpredict's message
			if not data:
				break

			cmd = data.decode("utf-8").strip().split(" ")   #grab the incoming command

			print("Received: ", cmd)    #debugging, what did Gpredict send?

			if cmd[0] == "p":   #Gpredict is requesting current position
				command = ('&* AZ=?\r').encode('ascii')
				antenna.write(command)
				res = antenna.read(200).decode(errors='ignore').strip()
				az_pattern = r"AZ=(\d+\.\d+)"
				az_match = re.search(az_pattern, res)

				command = ('&* EL=?\r').encode('ascii')
				antenna.write(command)
				res = antenna.read(200).decode(errors='ignore').strip()
				el_pattern = r"EL=(\d+\.\d+)"
				el_match = re.search(el_pattern, res)

				if az_match and el_match:
					az = float(az_match.group(1))
					el = float(el_match.group(1))
					response = "{}\n{}\n".format(az, el)
					print('response: '+ response)
					conn.send(response.encode('utf-8'))

			elif cmd[0] == "P":   #Gpredict is sending desired position
				target_az = cmd[1]
				target_el = cmd[2]
				#Tell Gpredict things went correctly
				command = ('&* AZ='+target_az+'\r').encode('ascii')
				antenna.write(command)
				command = ('&* EL='+target_el+'\r').encode('ascii')
				antenna.write(command)

				response="RPRT 0\n "  #Everything's under control, situation normal
				conn.send(response.encode('utf-8'))

			elif cmd[0] == "S":
				print('Gpredict disconnected')
				break  # Beende den Thread


		except Exception as e:
			print(f"Error handling connection: {e}")
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
	antenna = serial.Serial(
		port=serial_port,
		baudrate=1200,
		bytesize=serial.EIGHTBITS,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		timeout=1
	)


	try:
		start_server()
	except KeyboardInterrupt:
		print("Shutting down.")

