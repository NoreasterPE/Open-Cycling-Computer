import RPi.GPIO as GPIO

class bmp183():
	'Class for BMP183 pressure and temperature sensor'

	self.MOSI = 10  # GPIO for MOSI
	self.MISO = 9   # GPIO for MISO
	self.SCLK = 11  # GPIO for Clock
	self.CE   = 8   # GPIO for Chip Enable

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
		# Read TEMPERATURE, Wait time 4.5 ms
		TEMP  = 0x2E

		# Read PRESSURE
		PRESS = 0x34 #001
		
		OVERSAMPLE_0 = 0x00 # ultra low power, no oversampling, wait time 4.5 ms
		OVERSAMPLE_1 = 0x40 # standard, 2 internal samples, wait time 7.5 ms
		OVERSAMPLE_2 = 0x80 # high resolution, 4 internal samples, wait time 13.5 ms
		OVERSAMPLE_3 = 0xC0 # ultra high resolution, 8 internal samples, Wait time 25.5 ms
		# Usage: (PRESS || OVERSAMPLE_2)

		#FIXME How ADVANCED RESOLUTION mode works? Page 13 of data sheet,  wait time 76.5 ms
	}

	#start

	# GPIO initialisation
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(self.SCLK, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(self.CE, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(self.MOSI, GPIO.OUT)
	GPIO.setup(self.MISO, GPIO.IN)

	#start TEMP measurement
	GPIO.output(self.CE, 0)

GPIO.input(channel)
GPIO.output(channel, state)
	#wait 4.5

	#read uncmpensated temperature u_temp

	#start pressure measurement

	#wait (depend on mode)

	#read uncmpensated pressure u_press

	#calculate real temperature r_temp

	#calculate real pressure r_press

	#end
	GPIO.cleanup(self.SCLK)
	GPIO.cleanup(self.CE)
	GPIO.cleanup(self.MOSI)
	GPIO.cleanup(self.MISO)


 
 
int main (void)
{
    int a,b,loop,delay;
    int val[100000];
    double vin;
    int a2dChannel=0;
    int bits[3]={2,7,7};
    char tx[3], rx[3];
    struct timespec start;
    struct timespec end;
    unsigned long nanodif;
    time_t secdif;
   
    if (gpioInitialise() < 0) return 1;
   
   printf("GPIO pins initialised\n");
   
##   gpioSetMode(MOSI, 1);    // set MOSI to output
##   gpioSetMode(MISO, 0);    // set MISO to input
##   gpioSetMode(SCLK, 1);    // set SCLK to output
##   gpioSetMode(CE, 1);    // set CE to output
##   gpioWrite(CE,1);        // set chip enable high
##    gpioWrite(SCLK,1);     // set clock high
       
    printf("Set GPIO pin directions\n");

   clock_gettime(CLOCK_REALTIME, &start);
   
    for (loop=0; loop<100000; loop++)
    {
      gpioWrite(CE,0);  // set chip enable low so ADC will take notice   

      // setup transmit and recieve bytes
   
      tx[0] = (6 |( ((a2dChannel & 7) >>2)))<<5; // trim off the first 5 bits for speed!
      tx[1] = 0 |( ((a2dChannel & 3) << 6));
      tx[2] = 0;
      rx[0] = 0;
      rx[1] = 0;
      rx[2] = 0;
   
      for(a=0; a<3; a++)            // there are 3 bytes to send
      {
         for(b=bits[a]; b>=0; b--)   // loop 8 times for each byte
         {
            if(tx[a]& 0x80)       // if bit 7 of tx[a] is a 1
               gpioWrite(MOSI,1);    // set mosi high
            else
               gpioWrite(MOSI,0);    // else set mosi low

            gpioWrite(SCLK,0);      // Set clock low to tell the ADC to read MOSI
            
            for(delay=0; delay<100; delay++);         
            
            if(gpioRead(MISO)) rx[a]=rx[a]|(0x1<<(b));    // if MISO is high shift left and or it with rx byte         
                  
            gpioWrite(SCLK,1);       // Set clock back high ready for next loop

            tx[a] = tx[a]<<1;       // shift tx bits one place left
         }
      }
   
      val[loop] = ((rx[1] & 15 ) << 8) | (rx[2] & 255);


   
      gpioWrite(CE,1);              // reset chip enable high
   }   
   
   clock_gettime(CLOCK_REALTIME, &end);

    secdif=end.tv_sec - start.tv_sec;
    nanodif = end.tv_nsec - start.tv_nsec;
   
   if(nanodif<0)
    {
      secdif--;
      nanodif=0-nanodif;
   }
   
    printf("Start time : %ld.%ld   End time %ld.%ld \n" ,(long) start.tv_sec, (long) start.tv_nsec, (long) end.tv_sec, (long) end.tv_nsec);
    printf("Time taken : %ld.%ld seconds \n", (long) secdif, (long) nanodif);
   
    for(loop=0; loop<20; loop++) printf("ADC returned  %u\n",val[loop]);
   
   
    return 0;
}
