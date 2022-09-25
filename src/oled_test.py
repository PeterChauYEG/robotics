import time
import qwiic
import subprocess

LCDWIDTH = 64


def get_ip_address():
    ip = subprocess.check_output(['hostname', '-I'])
    return ip.decode('utf-8').split(' ')[0]


def get_resource_usage():
    # CPU Load
    cmd = "top -bn1 | grep load | awk '{printf \"%.1f%%\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell=True)

    # Memory Use
    cmd = "free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}'"
    Mem_percent = subprocess.check_output(cmd, shell=True)

    # Disk Storage
    cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
    Disk_percent = subprocess.check_output(cmd, shell=True)

    return CPU, Mem_percent, Disk_percent


def get_bit_text_spacing(display, bit):
    text_spacing = LCDWIDTH - (display._font.width + 1) * (len(str(bit.decode('utf-8'))))
    return text_spacing


def clear_display(display):
    display.clear(disp.PAGE)
    display.clear(disp.ALL)


def init_display(display):
    display.begin()
    display.scroll_stop()
    display.set_font_type(0)
    clear_display(display)


def display_ip(display, ip):
    display.set_cursor(0, 0)

    if ip:
        display.print("ip: ")
        display.set_cursor(0, 8)
        display.print(ip)
    else:
        display.print("No Internet!")

    display.display()
    time.sleep(5)
    clear_display(display)


def display_resource_usage(display, CPU, Mem_percent, Disk_percent):
    x3 = get_bit_text_spacing(disp, CPU)
    x4 = get_bit_text_spacing(disp, Mem_percent)
    x5 = get_bit_text_spacing(disp, Disk_percent)

    display.set_cursor(0, 0)
    display.print("CPU:")
    display.set_cursor(0, 10)
    display.print("Mem:")
    display.set_cursor(0, 20)
    display.print("Disk:")

    display.set_cursor(x3, 0)
    display.print(str(CPU.decode('utf-8')))
    display.set_cursor(x4, 10)
    display.print(str(Mem_percent.decode('utf-8')))
    display.set_cursor(x5, 20)
    display.print(str(Disk_percent.decode('utf-8')))

    display.display()
    time.sleep(2)
    clear_display(display)


if __name__ == '__main__':
    print('starting i2c test')

    disp = qwiic.QwiicMicroOled()

    init_display(disp)
    time.sleep(1)

    while True:
        ip = get_ip_address()
        CPU, Mem_percent, Disk_percent = get_resource_usage()

        display_ip(disp, ip)
        display_resource_usage(disp, CPU, Mem_percent, Disk_percent)
