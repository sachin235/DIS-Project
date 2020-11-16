# user 54321

import socket
import os
import subprocess

print("Enter your key")
my_secret_key = int(input())

s = socket.socket()
host = '192.168.1.108'
port = 9999

server_ip = None
server_port = 8888
session_key = None
message_for_server = None

try:
	s.connect((host, port))	
	print("Successfully Connected to KDC")
except Exception as e:
	print(e)

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

def help():
	print("Commands:")
	print("ls: To list all the files")
	print("getip <file_name>: To get the IP address of the file server that stores the file")
	print("getkey <Nonce> <Your User ID> <server IP address>: To get the session key of that server") #Use Nonce of two digits
	print("connect <Session key> <IP address of the server>: To the connect to the respective server")
	print("quit: To end connection to KDC and exit")

def connect():
	try:
		ss = socket.socket()
		print(server_ip)
		print(server_port)
		ss.connect((server_ip, server_port))
	except Exception as e:
		print(e)
		return

	print("Sending the encrypted session key")
	ss.send(str.encode(message_for_server))
	response = ss.recv(20480).decode("utf-8")
	response_decrypted = decrypt(response, session_key)

	if response_decrypted == "Invalid Request":
		print("Something Went Wrong")
		ss.close()
		return
	else:
		print("Nonce sent by server: " + str(response_decrypted))

	ss.send(str.encode(encrypt(str(int(response_decrypted)-1), session_key)))

	response = ss.recv(20480).decode("utf-8")
	response_decrypted = decrypt(response, session_key)

	if response_decrypted == "Invalid Request":
		print("Something Went Wrong")
		ss.close()
		return
	else:
		print("Connection to the server Successfull")

	while True:
		cmd = input(str(server_ip) + '> ')
		if cmd == "quit":
			ss.send(str.encode(encrypt(cmd,session_key)))
			ss.close()
			#sys.exit()
			break

		if len(str.encode(cmd)) > 0:
			ss.send(str.encode(encrypt(cmd,session_key)))
			client_response = str(ss.recv(20480), "utf-8")
			client_response = decrypt(client_response, session_key)
			print(client_response, end="")

while True:
	cmd = input("turtle> ")

	if cmd[:3] == "set":
		s.send(str.encode(cmd))

	elif cmd == "ls":
		s.send(str.encode(encrypt(cmd, my_secret_key)))
		server_response = s.recv(20480).decode("utf-8")
		server_response = decrypt(server_response, my_secret_key)
		print(server_response)

	elif cmd[:5] == "getip":
		s.send(str.encode(encrypt(cmd, my_secret_key)))
		server_ip = s.recv(20480).decode("utf-8")
		server_ip = decrypt(server_ip, my_secret_key)
		print(server_ip)

	elif cmd[:6] == "getkey":
		s.send(str.encode(encrypt(cmd, my_secret_key)))
		kdc_response = s.recv(20480).decode("utf-8")
		kdc_response = decrypt(kdc_response, my_secret_key)
		print(kdc_response)
		kdc_response = kdc_response.strip('][').split(', ') 

		nonce = int(kdc_response[0].replace('\'',''))
		session_key = int(kdc_response[1])
		server_ip = kdc_response[2].replace('\'','')
		message_for_server = kdc_response[3].replace('\'','')

		print("Nonce: " + str(nonce))
		print("Session Key: " + str(session_key))
		print("Server IP: " + server_ip)
		print("Encrypted Message for Server: " + message_for_server)

	elif cmd[:7] == "connect":
		connect()

	elif cmd == "quit":
		s.send(str.encode(encrypt("quit", my_secret_key)))
		s.close()
		break
