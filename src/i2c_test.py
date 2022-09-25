import qwiic

results = qwiic.list_devices()

print("Found %d devices" % len(results))

oled = qwiic.QwiicMicroOled()
oled.begin()

#Setup OLED
oled.clear(oled.ALL)
oled.display()
oled.set_font_type(1)
