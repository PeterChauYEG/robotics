import time
import qwiic_micro_oled
import subprocess

if __name__ == '__main__':
    print('starting i2c test')

    # Screen Width
    LCDWIDTH = 64

    # Initialization------------------------------------------------------------
    disp = qwiic_micro_oled.QwiicMicroOled()
    
    disp.begin()
    disp.scroll_stop()
    disp.set_font_type(0) # Set Font
    # Could replace line spacing with disp.getFontHeight, but doesn't scale properly

    # Display Flame (set in begin function)-------------------------------------
    disp.display()
    time.sleep(5) # Pause 5 sec

    while True:
        # # Checks Eth0 and Wlan0 Connections---------------------------------
        # a = 0
        # b = 0
        # c = 0
        #
        #
        # # Checks for Ethernet Connection
        # try:
        #     eth = get_ip_address('eth0')
        #     if eth != None:
        #         a = a + 1
        #
        #     #Check String Length
        #     if len(eth) > 10:
        #         # Find '.' to loop numerals
        #         while b != -1:
        #             x1 = LCDWIDTH - disp._font.width * (len(eth) - b)
        #             i = b + 1
        #             b = eth.find('.', i)
        #
        # except Exception as e:
        #     print(e)
        #
        # # Checks for WiFi Connection
        # try:
        #     wlan = get_ip_address('wlan0')
        #     if wlan != None:
        #         a = a + 2
        #
        #     #Check String Length
        #     if len(wlan) > 10:
        #         # Find '.' to loop numerals
        #         while c != -1:
        #             x2 = LCDWIDTH - disp._font.width * (len(wlan) - c)
        #             j = c + 1
        #             c = wlan.find('.', j)
        #
        # except Exception as e:
        #     print(e)


        # Check Resource Usage----------------------------------------------
        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-$

        # CPU Load
        cmd = "top -bn1 | grep load | awk '{printf \"%.1f%%\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell = True )

        # Memory Use
        cmd = "free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}'"
        Mem_percent = subprocess.check_output(cmd, shell = True )
        cmd = "free -m | awk 'NR==2{printf \"%.2f/%.1f\", $3/1024,$2/1024}'"
        MemUsage = subprocess.check_output(cmd, shell = True )

        # Disk Storage
        cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
        Disk_percent = subprocess.check_output(cmd, shell = True )
        cmd = "df -h | awk '$NF==\"/\"{printf \"%d/%d\", $3,$2}'"
        DiskUsage = subprocess.check_output(cmd, shell = True )


        # Text Spacing (places text on right edge of display)
        x3 = LCDWIDTH - (disp._font.width + 1) * (len(str(CPU.decode('utf-8'))))
        x4 = LCDWIDTH - (disp._font.width + 1) * (len(str(Mem_percent.decode('utf-8'))))
        x5 = LCDWIDTH - (disp._font.width + 1) * (len(str(Disk_percent.decode('utf-8'))))
        x6 = LCDWIDTH - (disp._font.width + 1) * (len(str(MemUsage.decode('utf-8')) + "GB"))
        x7 = LCDWIDTH - (disp._font.width + 1) * (len(str(DiskUsage.decode('utf-8')) + "GB"))

        # # Displays IP Address (if available)--------------------------------
        #
        # # Clear Display
        # disp.clear(disp.PAGE)
        # disp.clear(disp.ALL)
        #
        # #Set Cursor at Origin
        # disp.set_cursor(0,0)
        #
        # # Prints IP Address on OLED Display
        # if a == 1:
        #     disp.print("eth0:")
        #     disp.set_cursor(0,8)
        #     if b != 0:
        #         disp.print(str(eth[0:i]))
        #         disp.set_cursor(x1,16)
        #         disp.print(str(eth[i::]))
        #     else:
        #         disp.print(str(eth))
        #
        # elif a == 2:
        #     disp.print("wlan0: ")
        #     disp.set_cursor(0,8)
        #     if c != 0:
        #         disp.print(str(wlan[0:j]))
        #         disp.set_cursor(x2,16)
        #         disp.print(str(wlan[j::]))
        #     else:
        #         disp.print(str(wlan))
        #
        # elif a == 3:
        #     disp.print("eth0:")
        #     disp.set_cursor(0,8)
        #     if b != 0:
        #         disp.print(str(eth[0:i]))
        #         disp.set_cursor(x1,16)
        #         disp.print(str(eth[i::]))
        #     else:
        #         disp.print(str(eth))
        #
        #     disp.set_cursor(0,24)
        #     disp.print("wlan0: ")
        #     disp.set_cursor(0,32)
        #     if c != 0:
        #         disp.print(str(wlan[0:j]))
        #         disp.set_cursor(x2,40)
        #         disp.print(str(wlan[j::]))
        #     else:
        #         disp.print(str(wlan))
        #
        # else:
        #     disp.print("No Internet!")
        #
        # disp.display()
        # time.sleep(10) # Pause 10 sec

        # Displays Resource Usage-------------------------------------------
        # ------------------------------------------------------------------

        # Percentage--------------------------------------------------------
        # Clear Display
        disp.clear(disp.PAGE)
        disp.clear(disp.ALL)

        # Prints Percentage Use on OLED Display
        disp.set_cursor(0,0)	# Set Cursor at Origin
        disp.print("CPU:")
        disp.set_cursor(0,10)
        disp.print("Mem:")
        disp.set_cursor(0,20)
        disp.print("Disk:")

        disp.set_cursor(x3,0)
        disp.print(str(CPU.decode('utf-8')))
        disp.set_cursor(x4,10)
        disp.print(str(Mem_percent.decode('utf-8')))
        disp.set_cursor(x5,20)
        disp.print(str(Disk_percent.decode('utf-8')))

        disp.display()
        time.sleep(7.5) # Pause 7.5 sec


        # Size--------------------------------------------------------------
        # Clear Display
        disp.clear(disp.PAGE)
        disp.clear(disp.ALL)

        # Prints Capacity Use on OLED Display
        disp.set_cursor(0,0)	# Set Cursor at Origin
        disp.print("Mem:")
        disp.set_cursor(x6,10)
        disp.print(str(MemUsage.decode('utf-8')) + "GB")
        disp.set_cursor(0,20)
        disp.print("Disk:")
        disp.set_cursor(x7,30)
        disp.print(str(DiskUsage.decode('utf-8')) + "GB")

        disp.display()
        time.sleep(7.5) # Pause 7.5 sec
