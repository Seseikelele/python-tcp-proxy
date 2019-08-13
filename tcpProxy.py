#!/usr/bin/python3
import sys
import socket
import threading

def hexdump(buffer, length=20):
	result = []
	digits = 2 if isinstance(buffer, bytes) else 4
	for i in range(0, len(buffer), length):
		s = buffer[i:i + length]
		hexa = ' '.join(['%0*X' % (digits, ord(x)) for x in s])
		text = ''.join([x if 0x20 <= ord(x) < 0x7F else '.' for x in s])
		result.append('%04X   %-*s   %s' % (i, length * (digits + 1), hexa, text))
	print('\n'.join(result))

def requestHandler(buffer):
	return buffer

def responseHandler(buffer):
	return buffer

def receiveFrom(s):
	buffer = ''
	s.settimeout(2.0)
	try:
		while True:
			data = s.recv(4096)
			if not data:
				break
			buffer += data.decode()
	except:
		pass
	return buffer

def proxyHandler(s, host, port, recv):
	remoteSocket = socket.socket()
	print('[*] Connecting to remote host')
	remoteSocket.connect((host, port))
	print('[*] Connected to remote host')
	if recv:
		print('[*] receivefirst active')
		remoteBuffer = receiveFrom(remoteSocket)
		hexdump(remoteBuffer)
		remoteBuffer = responseHandler(remoteBuffer)
		if len(remoteBuffer):
			print('[<] Sending %d bytes to localhost' % len(remoteBuffer))
			s.send(remoteBuffer)
	while True:
		localBuffer = receiveFrom(s)
		if len(localBuffer):
			print('[>] Received %d bytes from localhost' % len(localBuffer))
			hexdump(localBuffer)
			localBuffer = requestHandler(localBuffer)
			print('[>] Sending to remote')
			remoteSocket.send(localBuffer.encode())
		remoteBuffer = receiveFrom(remoteSocket)
		if len(remoteBuffer):
			print('[<] Received %d bytes from remote' % len(remoteBuffer))
			hexdump(remoteBuffer)
			remoteBuffer = responseHandler(remoteBuffer)
			print('[<] Sending to localhost')
			s.send(remoteBuffer.encode())
		if not len(localBuffer) or not len(remoteBuffer):
			print('[*] No more data, closing connections')
			remoteSocket.close()
			s.close()
			break


def serverLoop(localHost, localPort, remoteHost, remotePort, receiveFirst):
	srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		srv.bind((localHost, localPort))
	except Exception as err:
		print('[!] Failed to start server on %s:%d' % (localHost, localPort))
		print(err)
		sys.exit(1)

	print('[*] Listening on %s:%d' % (localHost, localPort))
	srv.listen(5)

	while True:
		client, address = srv.accept()
		print('[>] Received connection from %s:%d' % (address[0], address[1]))
		proxyThread = threading.Thread(target=proxyHandler, args=(client, remoteHost, remotePort, receiveFirst))
		proxyThread.start()

def main():
	if len(sys.argv[1:]) != 5:
		print('Usage: %s [local_host] [local_port] [remote_host] [remote_port] [receive_first]' % (sys.argv[0]))
		print('Example: %s 127.0.0.1 1337 192.168.0.13 8080 True' % (sys.argv[0]))
		sys.exit(2)

	localHost = sys.argv[1]
	localPort = int(sys.argv[2])
	remoteHost = sys.argv[3]
	remotePort = int(sys.argv[4])
	receiveFirst = sys.argv[5] == 'True'

	serverLoop(localHost, localPort, remoteHost, remotePort, receiveFirst)

try:
	main()
except KeyboardInterrupt:
	sys.exit(0)