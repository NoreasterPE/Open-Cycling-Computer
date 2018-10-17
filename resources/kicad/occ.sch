EESchema Schematic File Version 2
LIBS:occ-rescue
LIBS:power
LIBS:device
LIBS:switches
LIBS:relays
LIBS:motors
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:occ
LIBS:occ-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Open Cycling Computer"
Date "WORK IN PROGRESS"
Rev "v0.01"
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 "CC-BY-SA"
$EndDescr
$Comp
L raspberry-pi-zero-w-RESCUE-occ RPI
U 1 1 5BA78832
P 3475 4700
F 0 "RPI" H 3500 5775 60  0000 C CNN
F 1 "raspberry-pi-zero-w" H 3500 5700 60  0000 C CNN
F 2 "" H 3250 5275 60  0001 C CNN
F 3 "" H 3250 5275 60  0001 C CNN
	1    3475 4700
	1    0    0    -1  
$EndComp
$Comp
L bmp_183 BMP183
U 1 1 5BA7E34A
P 5425 5400
F 0 "BMP183" H 5475 5550 60  0000 C CNN
F 1 "bmp_183" H 5450 5450 60  0000 C CNN
F 2 "" H 5275 5375 60  0001 C CNN
F 3 "" H 5275 5375 60  0001 C CNN
	1    5425 5400
	1    0    0    -1  
$EndComp
$Comp
L adafruit-pitft-2.8-res-RESCUE-occ PiTFT_320x240
U 1 1 5BA7D28E
P 3525 3050
F 0 "PiTFT_320x240" H 3500 3375 60  0000 C CNN
F 1 "adafruit-pitft-2.8-res" H 3500 3300 60  0000 C CNN
F 2 "" H 3300 3625 60  0001 C CNN
F 3 "" H 3300 3625 60  0001 C CNN
	1    3525 3050
	1    0    0    -1  
$EndComp
$Comp
L pimoroni-lipo-shim LIPO-SHIM
U 1 1 5BA7F39B
P 5750 3000
F 0 "LIPO-SHIM" H 5750 3150 60  0000 C CNN
F 1 "pimoroni-lipo-shim" H 5750 3050 60  0000 C CNN
F 2 "" H 5625 2625 60  0001 C CNN
F 3 "" H 5625 2625 60  0001 C CNN
	1    5750 3000
	-1   0    0    -1  
$EndComp
Wire Wire Line
	4575 4600 4350 4600
Wire Wire Line
	4575 2900 4575 4600
Wire Wire Line
	4525 4800 4350 4800
Wire Wire Line
	4525 3000 4525 4800
Wire Wire Line
	4475 4900 4350 4900
Wire Wire Line
	4475 3100 4475 4900
Wire Wire Line
	4425 5000 4350 5000
Wire Wire Line
	4425 3200 4425 5000
Wire Wire Line
	4775 3050 4775 3800
Wire Wire Line
	4775 3800 4775 5100
Wire Wire Line
	4775 5100 4825 5100
Wire Wire Line
	4775 3800 4350 3800
Wire Wire Line
	4725 5300 4825 5300
Wire Wire Line
	4725 3150 4725 4000
Wire Wire Line
	4725 4000 4725 5300
Wire Wire Line
	4725 4000 4350 4000
Wire Wire Line
	4825 5400 4575 5400
Wire Wire Line
	4575 5400 4575 5300
Wire Wire Line
	4575 5300 4350 5300
Wire Wire Line
	4825 5500 4350 5500
Wire Wire Line
	4825 5600 4350 5600
Wire Wire Line
	4825 5700 4350 5700
Wire Wire Line
	4425 3200 4275 3200
Wire Wire Line
	4475 3100 4275 3100
Wire Wire Line
	4525 3000 4275 3000
Wire Wire Line
	4575 2900 4275 2900
Wire Wire Line
	2475 4700 2475 2900
Wire Wire Line
	2475 2900 2700 2900
Wire Wire Line
	2700 3100 2575 3100
Wire Wire Line
	2525 4800 2525 3000
Wire Wire Line
	2525 3000 2700 3000
Wire Wire Line
	2675 4700 2475 4700
Wire Wire Line
	2675 4800 2525 4800
Wire Wire Line
	2575 4900 2675 4900
Wire Wire Line
	2575 3100 2575 4900
Connection ~ 4775 3800
Connection ~ 4725 4000
Wire Wire Line
	4850 3300 4850 3600
Wire Wire Line
	4900 3400 4900 3550
$Comp
L adafruit-usb-lipo-charger USB-CHARGER
U 1 1 5BA805B0
P 7850 3000
F 0 "USB-CHARGER" H 7900 2750 60  0000 C CNN
F 1 "adafruit-usb-lipo-charger" H 7950 2650 60  0000 C CNN
F 2 "" H 7725 2725 60  0001 C CNN
F 3 "" H 7725 2725 60  0001 C CNN
	1    7850 3000
	1    0    0    -1  
$EndComp
Wire Wire Line
	7000 3050 6950 3050
Wire Wire Line
	6950 3050 6950 3550
Wire Wire Line
	6950 3550 4900 3550
Wire Wire Line
	4850 3600 7000 3600
Wire Wire Line
	7000 3600 7000 3150
Wire Wire Line
	7000 3150 7000 3150
$Comp
L Battery LIPO-BATT
U 1 1 5BA80810
P 7000 2525
F 0 "LIPO-BATT" H 7100 2625 50  0000 L CNN
F 1 "Battery" H 7100 2525 50  0000 L CNN
F 2 "" V 7000 2585 50  0001 C CNN
F 3 "" V 7000 2585 50  0001 C CNN
	1    7000 2525
	1    0    0    1   
$EndComp
Wire Wire Line
	7000 2725 7000 2850
Wire Wire Line
	6850 2950 7000 2950
Wire Wire Line
	4950 3400 4900 3400
Wire Wire Line
	4950 3300 4850 3300
Wire Wire Line
	4950 3050 4775 3050
Wire Wire Line
	4950 3150 4725 3150
Text Notes 2800 2650 0    60   ~ 0
Common 2x20 header with RPI
Text Notes 5050 2750 0    60   ~ 0
Common 2x20 header with RPI
Text Notes 4975 4950 0    60   ~ 0
Pressure and temperature\nsensor
Text Notes 6375 2250 0    60   ~ 0
2500mAh LiPo, 3.7V
Wire Wire Line
	7000 2325 7000 2300
Wire Wire Line
	7000 2300 6850 2300
Wire Wire Line
	6850 2300 6850 2950
$EndSCHEMATC
