import socket
import sys
import random
import threading
from queue import Queue

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()

all_connections = []
all_address = []
all_client_id = []

map_server_key = {'192.168.1.108': 14} # IP address of the server and respective key, key is not a multiple 10
map_client_key = {'12345': 15, '54321': 16} #User ID of size 5 and respective key

map_file_name_server = {'KDC.py': '192.168.1.108', 'server.py': '192.168.1.108', 'client.py': '192.168.1.108', 'new': '192.168.1.108'} # File name to respective server

def encrypt(s, key):
	key = key % 26
	encrypted_text = ""
	for i in s:
		if i >= 'a' and i <= 'z':
			encrypted_text = encrypted_text + chr(((ord(i)-ord('a')+key+26)%26)+ord('a'))
		elif i >= '0' and i <= '9':
			encrypted_text = encrypted_text + chr(((ord(i)-ord('0')+key+10)%10)+ord('0'))
		else:
			encrypted_text = encrypted_text + i

	return encrypted_text

def decrypt(s, key):
	key = key % 26
	decrypted_text = ""
	for i in s:
		if i >= 'a' and i <= 'z':
			decrypted_text = decrypted_text + chr(((ord(i)-ord('a')-key+26)%26)+ord('a'))
		elif i >= '0' and i <= '9':
			decrypted_text = decrypted_text + chr(((ord(i)-ord('0')-key+10)%10)+ord('0'))
		else:
			decrypted_text = decrypted_text + i

	return decrypted_text

# create a socket (connect two computers)
def create_socket():

	try:
		global host
		global port
		global s

		host = ""
		port = 9999
		s = socket.socket()

	except socket.error as msg:
		print("Socket Creation Error " + str(msg))

# binding the socket and listening for connections
def bind_socket():
	try:
		global host
		global port
		global s

		print("Binding the port " + str(port))

		s.bind((host, port))
		s.listen(5)

	except socket.error as msg:
		print("Socket Binding Error " + str(msg) + "\n" + "Retrying....")
		bind_socket()

# handling connections from multiple clients and saving to a list
# closing previous connections when server.py file is restarted
def accepting_connections():
	for c in all_connections:
		c.close()

	del all_connections[:]
	del all_address[:]

	while True:
		try:
			conn, address = s.accept()
			s.setblocking(1) # prevents timeout

			all_connections.append(conn)
			all_address.append(address)
			all_client_id.append(None)

			print("Connection has been established: " + address[0] + " Port " + str(address[1]))

		except:
			print("Error accepting connections")

# 2nd thread functions
# 1) Listing out all the clients
# 2) Select a client
# 3) Send commands to the client
# Interactive prompt for sending commands
def start_turtle():
	while True:
		listen_for_requests()

def create_session(client_response):
	nonce = client_response[7:9]
	client = client_response[10:15]
	server = client_response[16:]
	client_key = map_client_key[client]
	server_key = map_server_key[server]

	message = []
	message.append(nonce)
	session_key = random.randint(10,99) % 26
	if session_key < 10:
		session_key = session_key + 10

	message.append(session_key)
	message.append(server)
	message.append(encrypt(str(session_key) + " " + str(client), server_key))

	string_message = encrypt(str(message), client_key)
	return string_message


# display all current active connections with the client
def listen_for_requests():
	
	for i, conn in enumerate(all_connections):
		try:
			#conn.send(str.encode("Is Active"))
			#conn.settimeout(2.0)
			#print(str(all_address[i][0]) + " " + str(all_address[i][1]))
			conn.settimeout(1)
			client_response = conn.recv(20480).decode("utf-8")

			if client_response[:3] == "set":
				all_client_id[i] = client_response[4:]
				continue

			if all_client_id[i] is None or map_client_key[all_client_id[i]] is None:
				conn.send(str.encode("Please set a valid User ID first"))
				continue

			client_key = map_client_key[all_client_id[i]]
			client_response = decrypt(client_response, client_key)
			print(client_response)

			if client_response == "ls":
				conn.send(str.encode(encrypt(str(map_file_name_server.keys()), client_key)))

			elif client_response[:5] == "getip":
				try:
					map_file_name_server[client_response[6:]]
				except Exception as e:
					conn.send(str.encode(encrypt("Invalid File Name", client_key)))
					continue

				conn.send(str.encode(encrypt(map_file_name_server[client_response[6:]], client_key)))

			elif client_response[:6] == "getkey":
				try:
					map_client_key[client_response[10:15]]
				except Exception as e:
					conn.send(str.encode(encrypt("Invalid User ID", client_key)))
					continue

				try:
					map_server_key[client_response[16:]]
				except Exception as e:
					conn.send(str.encode(encrypt("Invalid IP address", client_key)))
					continue

				message = create_session(client_response)
				print(message)
				conn.send(str.encode(message))

			elif client_response == "quit":
				conn.close()
				del all_connections[i]
				del all_address[i]
				del all_client_id[i]
				break
			else:
				conn.send(encrypt("Invalid request!", client_key))

		except Exception as e:
			#print(e)
			#del all_connections[i]
			#del all_address[i]
			continue

# create worker threads
def create_workers():
	for _ in range(NUMBER_OF_THREADS):
		t = threading.Thread(target=work)
		t.daemon = True
		t.start()

# do next job that is in the queue (handle connections, send commands)
def work():
	while True:
		x = queue.get()
		if x == 1:
			create_socket()
			bind_socket()
			accepting_connections()
		if x == 2:
			start_turtle()

		queue.task_done()

# to create jobs
def create_jobs():
	for x in JOB_NUMBER:
		queue.put(x)

	queue.join()

create_workers()
create_jobs()