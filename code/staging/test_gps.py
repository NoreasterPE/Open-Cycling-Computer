#!/usr/bin/python3

from gps_mtk3339 import gps_mtk3339
import time
import os

if __name__ == '__main__':
    gps = gps_mtk3339()
    gps.start()
    try:
        while True:
            os.system('clear')
            data = gps.get_data()
            print('latitude    ', data[0])
            print('longitude   ', data[1])
            print('time utc    ', data[4])
            print('fix time    ', data[7])
            print('altitude (m)', data[2])
            print('eps         ', data[10])
            print('epx         ', data[11])
            print('epv         ', data[12])
            print('ept         ', data[13])
            print('speed (m/s) ', data[3])
            print('climb       ', data[8])
            print('track       ', data[9])
            print('mode        ', gps.data.fix.mode)
            print
            sat = gps.data.satellites
            l = len(sat)
            total_sat_used = 0
            total_sat_visi = 0
            for i in sat:
                print(i)
                if i.used:
                    total_sat_used += 1
                if i.ss > 0:
                    total_sat_visi += 1

            print
            print("No of satellites: {} / {} / {}".format(total_sat_used, total_sat_visi, l))

            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        # FIXME possibly required on shutdown
        gps.stop()
        gps.join()
