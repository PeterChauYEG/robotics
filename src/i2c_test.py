import qwiic

#These values are used to give BME280 and CCS811 some time to take samples
initialize=True
n=2

oled = qwiic.QwiicMicroOled()
oled.begin()

#Setup OLED
oled.clear(oled.ALL)
oled.display()
oled.set_font_type(1)
