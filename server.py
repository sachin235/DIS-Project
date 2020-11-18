import socket
import sys
import threading
import os
import random
import subprocess
from queue import Queue

intial_dir = os.getcwd()
my_secret_key = 14

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()

all_connections = []
all_address = []
all_session_keys = []
all_working_dir = []

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
		print("Creating Socket")
		global host
		global port
		global s

		host = ""
		port = 8888
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

			emessage = conn.recv(20480).decode("utf-8")
			dmessage = decrypt(emessage, my_secret_key)
			print("Message sent by client: " + str(dmessage))
			session_key = None
			try:
				session_key = int(dmessage[:2])
				print("Session key sent by client: " + str(session_key))
				nonce = random.randint(10,20)
				if nonce < 10:
					nonce = nonce + 10

				print("Value of nonce generated: " + str(nonce))
				conn.send(str.encode(encrypt(str(nonce), session_key)))
				response = conn.recv(20480).decode("utf-8")
				response = decrypt(response, session_key)
				response = int(response)
				print("Value of nonce-1 sent by client: " + str(response))
				if response == nonce-1:
					# Verified Successfully
					conn.send(str.encode(encrypt("success",session_key)))
					print("Connection Verified")
				else:
					print("Here")
					conn.send(str.encode(encrypt("Invalid Request",session_key)))
					conn.close()
					continue


			except Exception as e:
				print(e)
				conn.send(str.encode(encrypt("Invalid Request",session_key)))
				conn.close()
				continue

			all_connections.append(conn)
			all_address.append(address)
			all_session_keys.append(session_key)
			all_working_dir.append(intial_dir)

			print("Connection has been established: " + address[0] + " Port " + str(address[1]))

		except:
			print("Error accepting connections")

def start_turtle():
	while True:
		for i, conn in enumerate(all_connections):
			try:
				conn.settimeout(1)
				client_query = conn.recv(20480).decode("utf-8")
				client_query = decrypt(client_query, all_session_keys[i])

				print(client_query)

				currentWD = all_working_dir[i]
				os.chdir(currentWD)
				if client_query == "quit":
					print("Closing connection to client")
					conn.close()
					del all_connections[i]
					del all_address[i]
					del all_session_keys[i]
					del all_working_dir[i]
					break

				if client_query[:2] == "cd":
					os.chdir(client_query[3:])
					all_working_dir[i] = os.getcwd()

				if len(client_query) > 0:
					cmd = subprocess.Popen(client_query[:], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
					output_byte = cmd.stdout.read()
					output_str = str(output_byte, "utf-8")
					currentWD = os.getcwd() + ">"
					conn.send(str.encode(encrypt(output_str + currentWD, all_session_keys[i])))

			#print(output_str)
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