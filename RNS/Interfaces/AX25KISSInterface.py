from __future__ import print_function
from Interface import Interface
from time import sleep
import sys
import serial
import threading
import time
import RNS

class KISS():
	FEND			  = chr(0xC0)
	FESC			  = chr(0xDB)
	TFEND			  = chr(0xDC)
	TFESC			  = chr(0xDD)
	CMD_UNKNOWN		  = chr(0xFE)
	CMD_DATA		  = chr(0x00)
	CMD_TXDELAY		  = chr(0x01)
	CMD_P			  = chr(0x02)
	CMD_SLOTTIME	  = chr(0x03)
	CMD_TXTAIL		  = chr(0x04)
	CMD_FULLDUPLEX	  = chr(0x05)
	CMD_SETHARDWARE	  = chr(0x06)
	CMD_READY         = chr(0x0F)
	CMD_RETURN		  = chr(0xFF)

class AX25():
	PID_NOLAYER3	= chr(0xF0)
	CTRL_UI			= chr(0x03)
	CRC_CORRECT     = chr(0xF0)+chr(0xB8)
	HEADER_SIZE		= 16


class AX25KISSInterface(Interface):
	MAX_CHUNK = 32768

	owner    = None
	port     = None
	speed    = None
	databits = None
	parity   = None
	stopbits = None
	serial   = None

	def __init__(self, owner, name, callsign, ssid, port, speed, databits, parity, stopbits, preamble, txtail, persistence, slottime, flow_control):
		self.serial   = None
		self.owner    = owner
		self.name	  = name
		self.src_call = callsign.upper()
		self.src_ssid = ssid
		self.dst_call = "APZRNS"
		self.dst_ssid = 0
		self.port     = port
		self.speed    = speed
		self.databits = databits
		self.parity   = serial.PARITY_NONE
		self.stopbits = stopbits
		self.timeout  = 100
		self.online   = False
		# TODO: Sane default and make this configurable
		self.txdelay  = 0.1

		self.packet_queue    = []
		self.flow_control    = flow_control
		self.interface_ready = False

		if (len(self.src_call) < 3 or len(self.src_call) > 6):
			raise ValueError("Invalid callsign for "+str(self))

		if (self.src_ssid < 0 or self.src_ssid > 15):
			raise ValueError("Invalid SSID for "+str(self))

		self.preamble    = preamble if preamble != None else 350;
		self.txtail      = txtail if txtail != None else 20;
		self.persistence = persistence if persistence != None else 64;
		self.slottime    = slottime if slottime != None else 20;

		if parity.lower() == "e" or parity.lower() == "even":
			self.parity = serial.PARITY_EVEN

		if parity.lower() == "o" or parity.lower() == "odd":
			self.parity = serial.PARITY_ODD

		try:
			RNS.log("Opening serial port "+self.port+"...")
			self.serial = serial.Serial(
				port = self.port,
				baudrate = self.speed,
				bytesize = self.databits,
				parity = self.parity,
				stopbits = self.stopbits,
				xonxoff = False,
				rtscts = False,
				timeout = 0,
				inter_byte_timeout = None,
				write_timeout = None,
				dsrdtr = False,
			)
		except Exception as e:
			RNS.log("Could not open serial port for interface "+str(self), RNS.LOG_ERROR)
			raise e

		if self.serial.is_open:
			# Allow time for interface to initialise before config
			sleep(2.0)
			thread = threading.Thread(target=self.readLoop)
			thread.setDaemon(True)
			thread.start()
			self.online = True
			RNS.log("Serial port "+self.port+" is now open")
			RNS.log("Configuring AX.25 KISS interface parameters...")
			self.setPreamble(self.preamble)
			self.setTxTail(self.txtail)
			self.setPersistence(self.persistence)
			self.setSlotTime(self.slottime)
			self.setFlowControl(self.flow_control)
			self.interface_ready = True
			RNS.log("AX.25 KISS interface configured")
			sleep(2)
		else:
			raise IOError("Could not open serial port")


	def setPreamble(self, preamble):
		preamble_ms = preamble
		preamble = int(preamble_ms / 10)
		if preamble < 0:
			preamble = 0
		if preamble > 255:
			preamble = 255

		kiss_command = KISS.FEND+KISS.CMD_TXDELAY+chr(preamble)+KISS.FEND
		written = self.serial.write(kiss_command)
		if written != len(kiss_command):
			raise IOError("Could not configure AX.25 KISS interface preamble to "+str(preamble_ms)+" (command value "+str(preamble)+")")

	def setTxTail(self, txtail):
		txtail_ms = txtail
		txtail = int(txtail_ms / 10)
		if txtail < 0:
			txtail = 0
		if txtail > 255:
			txtail = 255

		kiss_command = KISS.FEND+KISS.CMD_TXTAIL+chr(txtail)+KISS.FEND
		written = self.serial.write(kiss_command)
		if written != len(kiss_command):
			raise IOError("Could not configure AX.25 KISS interface TX tail to "+str(txtail_ms)+" (command value "+str(txtail)+")")

	def setPersistence(self, persistence):
		if persistence < 0:
			persistence = 0
		if persistence > 255:
			persistence = 255

		kiss_command = KISS.FEND+KISS.CMD_P+chr(persistence)+KISS.FEND
		written = self.serial.write(kiss_command)
		if written != len(kiss_command):
			raise IOError("Could not configure AX.25 KISS interface persistence to "+str(persistence))

	def setSlotTime(self, slottime):
		slottime_ms = slottime
		slottime = int(slottime_ms / 10)
		if slottime < 0:
			slottime = 0
		if slottime > 255:
			slottime = 255

		kiss_command = KISS.FEND+KISS.CMD_SLOTTIME+chr(slottime)+KISS.FEND
		written = self.serial.write(kiss_command)
		if written != len(kiss_command):
			raise IOError("Could not configure AX.25 KISS interface slot time to "+str(slottime_ms)+" (command value "+str(slottime)+")")

	def setFlowControl(self, flow_control):
		kiss_command = KISS.FEND+KISS.CMD_READY+chr(0x01)+KISS.FEND
		written = self.serial.write(kiss_command)
		if written != len(kiss_command):
			if (flow_control):
				raise IOError("Could not enable AX.25 KISS interface flow control")
			else:
				raise IOError("Could not enable AX.25 KISS interface flow control")


	def processIncoming(self, data):
		if (len(data) > AX25.HEADER_SIZE):
			self.owner.inbound(data[AX25.HEADER_SIZE:], self)


	def processOutgoing(self,data):
		if self.online:
			if self.interface_ready:
				if self.flow_control:
					self.interface_ready = False

				encoded_dst_ssid = 0x60 | (self.dst_ssid << 1)
				encoded_src_ssid = 0x60 | (self.src_ssid << 1) | 0x01

				addr = ""

				for i in range(0,6):
					if (i < len(self.dst_call)):
						addr += chr(ord(self.dst_call[i])<<1)
					else:
						addr += chr(0x20)
				addr += chr(encoded_dst_ssid)

				for i in range(0,6):
					if (i < len(self.src_call)):
						addr += chr(ord(self.src_call[i])<<1)
					else:
						addr += chr(0x20)
				addr += chr(encoded_src_ssid)

				data = addr+AX25.CTRL_UI+AX25.PID_NOLAYER3+data

				data = data.replace(chr(0xdb), chr(0xdb)+chr(0xdd))
				data = data.replace(chr(0xc0), chr(0xdb)+chr(0xdc))
				kiss_frame = chr(0xc0)+chr(0x00)+data+chr(0xc0)

				if (self.txdelay > 0):
					RNS.log(str(self.name)+" delaying TX for "+str(self.txdelay)+" seconds", RNS.LOG_EXTREME)
					sleep(self.txdelay)

				written = self.serial.write(kiss_frame)
				if written != len(kiss_frame):
					if self.flow_control:
						self.interface_ready = True
					raise IOError("AX.25 interface only wrote "+str(written)+" bytes of "+str(len(kiss_frame)))
			else:
				self.queue(data)

	def queue(self, data):
		self.packet_queue.append(data)

	def process_queue(self):
		if len(self.packet_queue) > 0:
			data = self.packet_queue.pop(0)
			self.interface_ready = True
			self.processOutgoing(data)
		elif len(self.packet_queue) == 0:
			self.interface_ready = True

	def readLoop(self):
		try:
			in_frame = False
			escape = False
			command = KISS.CMD_UNKNOWN
			data_buffer = ""
			last_read_ms = int(time.time()*1000)

			while self.serial.is_open:
				if self.serial.in_waiting:
					byte = self.serial.read(1)
					last_read_ms = int(time.time()*1000)

					if (in_frame and byte == KISS.FEND and command == KISS.CMD_DATA):
						in_frame = False
						self.processIncoming(data_buffer)
					elif (byte == KISS.FEND):
						in_frame = True
						command = KISS.CMD_UNKNOWN
						data_buffer = ""
					elif (in_frame and len(data_buffer) < RNS.Reticulum.MTU+AX25.HEADER_SIZE):
						if (len(data_buffer) == 0 and command == KISS.CMD_UNKNOWN):
							# We only support one HDLC port for now, so
							# strip off the port nibble
							byte = chr(ord(byte) & 0x0F)
							command = byte
						elif (command == KISS.CMD_DATA):
							if (byte == KISS.FESC):
								escape = True
							else:
								if (escape):
									if (byte == KISS.TFEND):
										byte = KISS.FEND
									if (byte == KISS.TFESC):
										byte = KISS.FESC
									escape = False
								data_buffer = data_buffer+byte
						elif (command == KISS.CMD_READY):
							# TODO: add timeout and reset if ready
							# command never arrives
							self.process_queue()
				else:
					time_since_last = int(time.time()*1000) - last_read_ms
					if len(data_buffer) > 0 and time_since_last > self.timeout:
			 			data_buffer = ""
			 			in_frame = False
			 			command = KISS.CMD_UNKNOWN
			 			escape = False
			 		sleep(0.08)

		except Exception as e:
			self.online = False
			RNS.log("A serial port error occurred, the contained exception was: "+str(e), RNS.LOG_ERROR)
			RNS.log("The interface "+str(self.name)+" is now offline. Restart Reticulum to attempt reconnection.", RNS.LOG_ERROR)

	def __str__(self):
		return "AX25KISSInterface["+self.name+"]"

