import RPi.GPIO as GPIO
#import sys
import time
import numpy

class bmp183():
	'Class for BMP183 pressure and temperature sensor'
	BMP183_REG = {
		'CAL_AC1' : 0xAA, 
		'CAL_AC2' : 0xAC,
		'CAL_AC3' : 0xAE,
		'CAL_AC4' : 0xB0,
		'CAL_AC5' : 0xB2,
		'CAL_AC6' : 0xB4,
		'CAL_B1': 0xB6,
		'CAL_B2': 0xB8, 
		'CAL_MB': 0xBA,
		'CAL_MC': 0xBC,
		'CAL_MD': 0xBE,
		#@ Chip ID. Value fixed to 0x55. Usefull to check if communication works
		'ID' : 0xD0,

		#@ VER FIXME Undocumented
		'VER' : 0xD1,

		#@ SOFT_RESET
		# Write only. If set to 0xB6, will perform the same sequence as power on reset.
		'SOFT_RESET' : 0xE0,

		#@ CTRL_MEAS
		# Controls the pressure measurement
		'CTRL_MEAS' : 0xF4,

		#@ DATA
		'DATA' : 0xF6,
	};

	BMP183_CMD = {
		'READWRITE' : 0x80,

		# Read TEMPERATURE, Wait time 4.5 ms
		'TEMP'  : 0x2E,

		# Read PRESSURE
		'PRESS' : 0x34, #001
		
		'OVERSAMPLE_0' : 0x00, # ultra low power, no oversampling, wait time 4.5 ms
		'OVERSAMPLE_1' : 0x40, # standard, 2 internal samples, wait time 7.5 ms
		'OVERSAMPLE_2' : 0x80, # high resolution, 4 internal samples, wait time 13.5 ms
		'OVERSAMPLE_3' : 0xC0, # ultra high resolution, 8 internal samples, Wait time 25.5 ms
		# Usage: (PRESS || OVERSAMPLE_2)

		#FIXME How ADVANCED RESOLUTION mode works? Page 13 of data sheet,  wait time 76.5 ms
	}

	def __init__(self):
		self.real_temp = 0
		self.SCLK = 8  # GPIO for Clock
		self.MISO = 10  # GPIO for MISO
		self.MOSI = 12  # GPIO for MOSI
		self.CE   = 16  # GPIO for Chip Enable

		self.delay = 1/10000.0
		self.set_up_gpio()
		#start

		#Check comunication / read ID
		ret = self.read_byte(self.BMP183_REG['ID'])
		if ret != 0x55:
			print ("BMP183 returned ", ret, " instead of 0x55")

		self.read_calibration_data()
		#self.measure_temperature()

		#start pressure measurement
		self.write_byte(self.BMP183_REG['CTRL_MEAS'], self.BMP183_CMD['PRESS'] | self.BMP183_CMD['OVERSAMPLE_0'], 8)
		#wait 4.5 ms
		time.sleep(0.0045)
		#wait for 0 on bit 5 in CTRL_MEAS, end of conversion (probably unnecesary wait)
		stop = 0 
		ret = 0x10
		while (stop != 10) and (ret & 0x10):
			ret = self.read_byte(self.BMP183_REG['CTRL_MEAS'])
			#print "Counting...:", stop, " ", ret
			stop = stop + 1
			time.sleep(0.005)

		#read uncmpensated pressure u_press
		self.UP = numpy.int32(self.read_word(self.BMP183_REG['DATA']))
#		print "UP ", self.UP
		#debug
#		self.UP = 23843

		#wait (depend on mode)

		#calculate real temperature r_temp
		self.measure_temperature()

		#calculate real pressure r_press
		self.OSS = 0

		#print "B5 ", self.B5
		self.B6 = self.B5 - 4000
	#	print "B6 ", self.B6
		self.X1 = (self.B2 * (self.B6 * self.B6 / 2**12))/2**11
	#	print "X1 ", self.X1
		self.X2 = self.AC2 * self.B6 / 2**11
	#	print "X2 ", self.X2
		self.X3 = self.X1 + self.X2
	#	print "X3 ", self.X3
		self.B3 = (((self.AC1 * 4 + self.X3) << self.OSS) + 2 )/4
	#	print "B3 ", self.B3
		self.X1 = self.AC3 * self.B6 / 2**13
	#	print "X1 ", self.X1
		self.X2 = (self.B1 * (self.B6 * self.B6 / 2**12))/2**16
	#	print "X2 ", self.X2
		self.X3 = ((self.X1 + self.X2) + 2)/2**2
	#	print "X3 ", self.X3
		self.B4 = numpy.uint32(self.AC4 * (self.X3 + 32768)/2**15)
	#	print "B4 ", self.B4
		self.B7 = (numpy.uint32(self.UP) - self.B3)*(50000 >> self.OSS)
	#	print "B7 ", self.B7
		#if (self.B7 < 0x80000000):
		p = numpy.uint32((self.B7 * 2)/self.B4)
		#else:
		#	p = numpy.uint64((self.B7 / self.B4) * 2)
	#	print "p ", p
		self.X1 = (p / 2**8)*( p / 2**8)
	#	print "X1 ", self.X1
		self.X1 = int(self.X1 * 3038) / 2**16
	#	print "X1 ", self.X1
		self.X2 = int(-7357 * p)/2**16
	#	print "X2 ", self.X2
		self.pressure = p + (self.X1 + self.X2 +3791)/2**4
		print "pressure", self.pressure


		#end

	def quit(self):
		self.cleanup_gpio()

	def set_up_gpio(self):
		# GPIO initialisation
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.SCLK, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.setup(self.CE, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.setup(self.MOSI, GPIO.OUT)
		GPIO.setup(self.MISO, GPIO.IN)

	def cleanup_gpio(self):
		GPIO.cleanup(self.SCLK)
		GPIO.cleanup(self.CE)
		GPIO.cleanup(self.MOSI)
		GPIO.cleanup(self.MISO)

	def read_byte(self, addr):
		#print 'read_byte'
		ret_value = self.spi_transfer(addr, 0, 1, 8)	
		return ret_value

	def read_word(self, addr):
		#print 'read_word'
		ret_value = self.spi_transfer(addr, 0, 1, 16)	
		return ret_value

	def write_byte(self, addr, value, length):
		#print 'write_byte'
		self.spi_transfer(addr, value, 0, length)	
		
	def spi_transfer(self, addr, value, rw, length):
		#print 'spi_transfer'
		ret_value = 0
		if (rw == 0):
			spi_addr = addr & (~self.BMP183_CMD['READWRITE'])
			#print "addr: ", hex(addr), " spi_addr: ", hex(spi_addr), " value: ", hex(value), "length:", length
		else:
			spi_addr = addr | self.BMP183_CMD['READWRITE']
			#print "addr: ", hex(addr), " spi_addr: ", hex(spi_addr), "length:", length


		GPIO.output(self.CE, 0)
		time.sleep(self.delay)
		#Send address
		#sys.stdout.write('Sending addr: ')
		for i in range(8):
			bit = spi_addr & (0x01 << (7 - i))
			if (bit):
				#sys.stdout.write("1")
				GPIO.output(self.MOSI, 1)
			else:
				#sys.stdout.write("0")
				GPIO.output(self.MOSI, 0)
			GPIO.output(self.SCLK, 0)
			time.sleep(self.delay)
			GPIO.output(self.SCLK, 1)
			time.sleep(self.delay)
		#print(' ')

		if (rw == 1):
			#Read data
			#sys.stdout.write('Received: ')
			for i in range(length):
				GPIO.output(self.SCLK, 0)
				time.sleep(self.delay)
				bit = GPIO.input(self.MISO)
				#if (bit):
				#	sys.stdout.write("1")
				#else:
				#	sys.stdout.write("0")
				GPIO.output(self.SCLK, 1)
				ret_value = (ret_value << 1) | bit
				time.sleep(self.delay)
			#print(' ')
			#print 'ret_value: ', hex(ret_value)

		if (rw == 0):
			#print('Writing:')
			#print(hex(value))
			for i in range(length):
				bit = value & (0x01 << (length - 1 - i))
				if (bit):
				#	sys.stdout.write("1")
					GPIO.output(self.MOSI, 1)
				else:
				#	sys.stdout.write("0")
					GPIO.output(self.MOSI, 0)
				GPIO.output(self.SCLK, 0)
				time.sleep(self.delay)
				GPIO.output(self.SCLK, 1)
				time.sleep(self.delay)
			#print(' ')
		GPIO.output(self.CE, 1)
		return ret_value

	def read_calibration_data(self):
		#Read calibration data
		self.AC1 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC1']))
		self.AC2 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC2']))
		self.AC3 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC3']))
		self.AC4 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC4']))
		self.AC5 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC5']))
		self.AC6 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC6']))
		self.B1 = numpy.int16(self.read_word(self.BMP183_REG['CAL_B1']))
		self.B2 = numpy.int16(self.read_word(self.BMP183_REG['CAL_B2']))
		self.MB = numpy.int16(self.read_word(self.BMP183_REG['CAL_MB']))
		self.MC = numpy.int16(self.read_word(self.BMP183_REG['CAL_MC']))
		self.MD = numpy.int16(self.read_word(self.BMP183_REG['CAL_MD']))
#debug
#		self.AC1 =  408
#		self.AC2 = -72
#		self.AC3 = -14383
#		self.AC4 = 32741
#		self.AC5 = 32757
#		self.AC6 = 23153
#		self.B1 = 6190
#		self.B2 = 4 
#		self.MB = -32767
#		self.MC = -8711 
#		self.MD = 2868 

	def calculate_real_temperature(self):
#debug
#		self.UT =  27898
		#Calculate real temperature
		self.X1 = (self.UT - self.AC6) * self.AC5 / 2**15
		self.X2 = self.MC * 2**11/(self.X1 + self.MD) 
		self.B5 = self.X1 + self.X2
		self.T = (self.B5 + 8)/2**4
		self.real_temp = self.T / 10.0

	def measure_temperature(self):
		#start TEMP measurement
		self.write_byte(self.BMP183_REG['CTRL_MEAS'], self.BMP183_CMD['TEMP'], 8)
		#wait 4.5 ms
		time.sleep(0.0045)
		#wait for 0 on bit 5 in CTRL_MEAS, end of conversion (probably unnecesary wait)
		stop = 0 
		ret = 0x10
		while (stop != 10) and (ret & 0x10):
			ret = self.read_byte(self.BMP183_REG['CTRL_MEAS'])
			#print "Counting...:", stop, " ", ret
			stop = stop + 1
			time.sleep(0.005)

		#read uncmpensated temperature u_temp
		self.UT = numpy.int32(self.read_word(self.BMP183_REG['DATA']))
#		print "UT ", self.UT
		self.calculate_real_temperature()
		#print "Temperature: ", self.real_temp

if __name__ == "__main__":
	bmp = bmp183()
#	try:
#		while (bmp.real_temp < 25.0):
#			bmp.measure_temperature()
#			print "Temperature: ", bmp.real_temp
#			time.sleep(0.3)
#	except KeyboardInterrupt:
#		print "Keyboard Interrupt"
		
	bmp.quit()
	quit()

