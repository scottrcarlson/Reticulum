##########################################################
# This RNS example demonstrates a simple client/server   #
# echo utility. A client can send an echo request to the #
# server, and the server will respond by proving receipt #
# of the packet.                                         #
##########################################################

import argparse
import RNS

# Let's define an app name. We'll use this for all
# destinations we create. Since this echo example
# is part of a range of example utilities, we'll put
# them all within the app namespace "example_utilities"
APP_NAME = "example_utilitites"


##########################################################
#### Server Part #########################################
##########################################################

# This initialisation is executed when the users chooses
# to run as a server
def server(configpath):
	# We must first initialise Reticulum
	reticulum = RNS.Reticulum(configpath)
	
	# Randomly create a new identity for our echo server
	server_identity = RNS.Identity()

	# We create a destination that clients can query. We want
	# to be able to verify echo replies to our clients, so we
	# create a "single" destination that can receive encrypted
	# messages. This way the client can send a request and be
	# certain that no-one else than this destination was able
	# to read it. 
	echo_destination = RNS.Destination(server_identity, RNS.Destination.IN, RNS.Destination.SINGLE, APP_NAME, "echo", "request")

	# We configure the destination to automatically prove all
	# packets adressed to it. By doing this, RNS will automatically
	# generate a proof for each incoming packet and transmit it
	# back to the sender of that packet.
	echo_destination.set_proof_strategy(RNS.Destination.PROVE_ALL)
	
	# Tell the destination which function in our program to
	# run when a packet is received. We do this so we can
	# print a log message when the server receives a request
	echo_destination.packet_callback(server_callback)

	# Everything's ready!
	# Let's Wait for client requests or user input
	announceLoop(echo_destination)


def announceLoop(destination):
	# Let the user know that everything is ready
	RNS.log("Echo server "+RNS.prettyhexrep(destination.hash)+" running, hit enter to manually send an announce (Ctrl-C to quit)")

	# We enter a loop that runs until the users exits.
	# If the user hits enter, we will announce our server
	# destination on the network, which will let clients
	# know how to create messages directed towards it.
	while True:
		entered = raw_input()
		destination.announce()
		RNS.log("Sent announce from "+RNS.prettyhexrep(destination.hash))


def server_callback(message, packet):
	# Tell the user that we received an echo request, and
	# that we are going to send a reply to the requester.
	# Sending the proof is handled automatically, since we
	# set up the destination to prove all incoming packets.
	RNS.log("Received packet from echo client, proof sent")


##########################################################
#### Client Part #########################################
##########################################################

# This initialisation is executed when the users chooses
# to run as a client
def client(destination_hexhash, configpath, timeout=None):
	# We need a binary representation of the destination
	# hash that was entered on the command line
	try:
		if len(destination_hexhash) != 20:
			raise ValueError("Destination length is invalid, must be 20 hexadecimal characters (10 bytes)")
		destination_hash = destination_hexhash.decode("hex")
	except:
		RNS.log("Invalid destination entered. Check your input!\n")
		exit()

	# We must first initialise Reticulum
	reticulum = RNS.Reticulum(configpath)

	# We override the loglevel to provide feedback when
	# an announce is received
	RNS.loglevel = RNS.LOG_INFO

	# Tell the user that the client is ready!
	RNS.log("Echo client ready, hit enter to send echo request to "+destination_hexhash+" (Ctrl-C to quit)")

	# We enter a loop that runs until the user exits.
	# If the user hits enter, we will try to send an
	# echo request to the destination specified on the
	# command line.
	while True:
		raw_input()
		# To address the server, we need to know it's public
		# key, so we check if Reticulum knows this destination.
		# This is done by calling the "recall" method of the
		# Identity module. If the destination is known, it will
		# return an Identity instance that can be used in
		# outgoing destinations.
		server_identity = RNS.Identity.recall(destination_hash)
		if server_identity != None:
			# We got the correct identity instance from the
			# recall method, so let's create an outgoing
			# destination. We use the naming convention:
			# example_utilities.echo.request
			# This matches the naming we specified in the
			# server part of the code.
			request_destination = RNS.Destination(server_identity, RNS.Destination.OUT, RNS.Destination.SINGLE, APP_NAME, "echo", "request")

			# The destination is ready, so let's create a packet.
			# We set the destination to the request_destination
			# that was just created, and the only data we add
			# is a random hash.
			echo_request = RNS.Packet(request_destination, RNS.Identity.getRandomHash())

			# Send the packet! If the packet is successfully
			# sent, it will return a PacketReceipt instance.
			packet_receipt = echo_request.send()

			# If the user specified a timeout, we set this
			# timeout on the packet receipt, and configure
			# a callback function, that will get called if
			# the packet times out.
			if timeout != None:
				packet_receipt.set_timeout(timeout)
				packet_receipt.timeout_callback(packet_timed_out)

			# We can then set a delivery callback on the receipt.
			# This will get automatically called when a proof for
			# this specific packet is received from the destination.
			packet_receipt.delivery_callback(packet_delivered)

			# Tell the user that the echo request was sent
			RNS.log("Sent echo request to "+RNS.prettyhexrep(request_destination.hash))
		else:
			# If we do not know this destination, tell the
			# user to wait for an announce to arrive.
			RNS.log("Destination is not yet known. Wait for an announce to arrive and try again.")

# This function is called when our reply destination
# receives a proof packet.
def packet_delivered(receipt):
	if receipt.status == RNS.PacketReceipt.DELIVERED:
		rtt = receipt.rtt()
		if (rtt >= 1):
			rtt = round(rtt, 3)
			rttstring = str(rtt)+" seconds"
		else:
			rtt = round(rtt*1000, 3)
			rttstring = str(rtt)+" milliseconds"

		RNS.log("Valid reply received from "+RNS.prettyhexrep(receipt.destination.hash)+", round-trip time is "+rttstring)

# This function is called if a packet times out.
def packet_timed_out(receipt):
	if receipt.status == RNS.PacketReceipt.FAILED:
		RNS.log("Packet "+RNS.prettyhexrep(receipt.hash)+" timed out")


##########################################################
#### Program Startup #####################################
##########################################################

# This part of the program gets run at startup,
# and parses input from the user, and then starts
# the desired program mode.
if __name__ == "__main__":
	try:
		parser = argparse.ArgumentParser(description="Simple echo server and client utility")
		parser.add_argument("-s", "--server", action="store_true", help="wait for incoming packets from clients")
		parser.add_argument("-t", "--timeout", action="store", metavar="s", default=None, help="set a reply timeout in seconds", type=float)
		parser.add_argument("--config", action="store", default=None, help="path to alternative Reticulum config directory", type=str)
		parser.add_argument("destination", nargs="?", default=None, help="hexadecimal hash of the server destination", type=str)
		args = parser.parse_args()

		if args.server:
			configarg=None
			if args.config:
				configarg = args.config
			server(configarg)
		else:
			if args.config:
				configarg = args.config
			else:
				configarg = None

			if args.timeout:
				timeoutarg = float(args.timeout)
			else:
				timeoutarg = None

			if (args.destination == None):
				print("")
				parser.print_help()
				print("")
			else:
				client(args.destination, configarg, timeout=timeoutarg)
	except KeyboardInterrupt:
		print("")
		exit()