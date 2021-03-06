EESchema Schematic File Version 2
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
LIBS:occ-rescue
LIBS:occ
LIBS:occ-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Open Cycling Computer"
Date "WORK IN PROGRESS"
Rev "v0.02"
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 "CC-BY-SA"
$EndDescr
$Comp
L raspberry-pi-zero-w-RESCUE-occ RPI1
U 1 1 5BA78832
P 3525 4750
F 0 "RPI1" H 3550 5825 60  0000 C CNN
F 1 "raspberry-pi-zero-w" H 3550 5750 60  0000 C CNN
F 2 "" H 3300 5325 60  0001 C CNN
F 3 "" H 3300 5325 60  0001 C CNN
	1    3525 4750
	1    0    0    -1  
$EndComp
$Comp
L adafruit-pitft-2.8-res-RESCUE-occ PiTFT_320x240
U 1 1 5BA7D28E
P 3575 6600
F 0 "PiTFT_320x240" H 3550 6925 60  0000 C CNN
F 1 "adafruit-pitft-2.8-res" H 3550 6850 60  0000 C CNN
F 2 "" H 3350 7175 60  0001 C CNN
F 3 "" H 3350 7175 60  0001 C CNN
	1    3575 6600
	1    0    0    -1  
$EndComp
$Comp
L pimoroni-lipo-shim LIPO-SHIM1
U 1 1 5BA7F39B
P 6900 1875
F 0 "LIPO-SHIM1" H 6900 2025 60  0000 C CNN
F 1 "pimoroni-lipo-shim" H 6900 1925 60  0000 C CNN
F 2 "" H 6775 1500 60  0001 C CNN
F 3 "" H 6775 1500 60  0001 C CNN
	1    6900 1875
	-1   0    0    -1  
$EndComp
Wire Wire Line
	4800 4650 4400 4650
Wire Wire Line
	4700 4850 4400 4850
Wire Wire Line
	4700 6550 4700 4850
Wire Wire Line
	4600 4950 4400 4950
Wire Wire Line
	4600 6650 4600 4950
Wire Wire Line
	4500 5050 4400 5050
Wire Wire Line
	4500 6750 4500 5050
Wire Wire Line
	4900 3050 4900 3850
Wire Wire Line
	4500 6750 4325 6750
Wire Wire Line
	4600 6650 4325 6650
Wire Wire Line
	4700 6550 4325 6550
Wire Wire Line
	4800 6450 4325 6450
Wire Wire Line
	2450 4750 2450 6450
Wire Wire Line
	2450 6450 2750 6450
Wire Wire Line
	2750 6650 2650 6650
Wire Wire Line
	2550 4850 2550 6550
Wire Wire Line
	2550 6550 2750 6550
Wire Wire Line
	2725 4750 2450 4750
Wire Wire Line
	2725 4850 2550 4850
Wire Wire Line
	2650 4950 2725 4950
Wire Wire Line
	2650 6650 2650 4950
$Comp
L adafruit-usb-lipo-charger USB-CHARGER1
U 1 1 5BA805B0
P 9475 1875
F 0 "USB-CHARGER1" H 9525 1625 60  0000 C CNN
F 1 "adafruit-usb-lipo-charger" H 9575 1525 60  0000 C CNN
F 2 "" H 9350 1600 60  0001 C CNN
F 3 "" H 9350 1600 60  0001 C CNN
	1    9475 1875
	1    0    0    -1  
$EndComp
Wire Wire Line
	8350 1925 8625 1925
$Comp
L Battery LIPO-BATT1
U 1 1 5BA80810
P 8625 1400
F 0 "LIPO-BATT1" H 8725 1500 50  0000 L CNN
F 1 "Battery" H 8725 1400 50  0000 L CNN
F 2 "" V 8625 1460 50  0001 C CNN
F 3 "" V 8625 1460 50  0001 C CNN
	1    8625 1400
	1    0    0    1   
$EndComp
Wire Wire Line
	8625 1600 8625 1725
Wire Wire Line
	8475 1825 8625 1825
Wire Wire Line
	5750 1925 6100 1925
Wire Wire Line
	5850 2025 6100 2025
Text Notes 2850 6200 0    60   ~ 0
Common 2x20 header with RPI
Text Notes 6200 1625 0    60   ~ 0
Common 2x20 header with RPI
Text Notes 2550 1400 0    60   ~ 0
Pressure and temp.\nsensor
Text Notes 8000 1125 0    60   ~ 0
2500mAh LiPo, 3.7V
Wire Wire Line
	8625 1200 8625 1175
Wire Wire Line
	8625 1175 8475 1175
Wire Wire Line
	8475 1175 8475 1825
$Comp
L bmp_280 bmp_2801
U 1 1 5BFA8DC4
P 3000 1900
F 0 "bmp_2801" H 3050 2050 60  0000 C CNN
F 1 "bmp_280" H 3025 1950 60  0000 C CNN
F 2 "" H 2850 1875 60  0001 C CNN
F 3 "" H 2850 1875 60  0001 C CNN
	1    3000 1900
	0    -1   -1   0   
$EndComp
$Comp
L ds3231 ds32311
U 1 1 5BFA9620
P 4125 1900
F 0 "ds32311" H 4175 2050 60  0000 C CNN
F 1 "ds3231" H 4150 1950 60  0000 C CNN
F 2 "" H 3975 1875 60  0001 C CNN
F 3 "" H 3975 1875 60  0001 C CNN
	1    4125 1900
	0    -1   -1   0   
$EndComp
Text Notes 3825 1375 0    60   ~ 0
Real Time Clock
Wire Wire Line
	2700 2500 2700 3050
Wire Wire Line
	3825 3050 3825 2500
Wire Wire Line
	2900 2500 2900 3150
Wire Wire Line
	2900 3150 3925 3150
Wire Wire Line
	3925 3150 5000 3150
Wire Wire Line
	5000 3150 5850 3150
Wire Wire Line
	3925 3150 3925 2500
Wire Wire Line
	3000 2500 3000 3250
Wire Wire Line
	2400 3250 3000 3250
Wire Wire Line
	3000 3250 4025 3250
Wire Wire Line
	4025 3250 4025 2500
Wire Wire Line
	4125 3350 4125 2500
Wire Wire Line
	2500 3350 3200 3350
Wire Wire Line
	3200 3350 4125 3350
Wire Wire Line
	3200 3350 3200 2500
Wire Wire Line
	2725 3950 2500 3950
Connection ~ 3200 3350
Connection ~ 3000 3250
Connection ~ 3825 3050
Connection ~ 3925 3150
Wire Wire Line
	4400 4050 5000 4050
Wire Wire Line
	5000 4050 5000 3150
Wire Wire Line
	2725 4050 2400 4050
Wire Wire Line
	2500 3950 2500 3350
Wire Wire Line
	2400 4050 2400 3250
Wire Wire Line
	4800 4650 4800 6450
Wire Wire Line
	4900 3850 4400 3850
Wire Wire Line
	2700 3050 3825 3050
Wire Wire Line
	3825 3050 4900 3050
Wire Wire Line
	4900 3050 5750 3050
Wire Wire Line
	5750 3050 5750 1925
Connection ~ 4900 3050
Wire Wire Line
	5850 3150 5850 2025
Connection ~ 5000 3150
Wire Wire Line
	8625 2025 8475 2025
Wire Wire Line
	8475 2025 8475 2175
Wire Wire Line
	8475 2175 7650 2175
Wire Wire Line
	8350 1925 8350 2275
Wire Wire Line
	8350 2275 7650 2275
Wire Wire Line
	7650 2025 7750 2025
Wire Wire Line
	7750 2025 7750 3450
Wire Wire Line
	7750 3450 2600 3450
Wire Wire Line
	2600 3450 2600 4150
Wire Wire Line
	2600 4150 2725 4150
Wire Wire Line
	2700 3850 2700 3550
Wire Wire Line
	2700 3550 7850 3550
Wire Wire Line
	7850 3550 7850 1925
Wire Wire Line
	7850 1925 7650 1925
$EndSCHEMATC
