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


class Monitor:
    def __init__(self):
        self.display = None

    def get_bit_text_spacing(self, bit):
        text_spacing = LCDWIDTH - (self.display._font.width + 1) * (len(str(bit.decode('utf-8'))))
        return text_spacing

    def clear_display(self):
        self.display.clear(self.display.PAGE)
        self.display.clear(self.display.ALL)

    def init_display(self):
        self.display = qwiic.QwiicMicroOled()
        self.display.begin()
        self.display.scroll_stop()
        self.display.set_font_type(0)
        self.display.display()
        time.sleep(1)
        self.clear_display()

    def display_ip(self, ip):
        self.display.set_cursor(0, 0)

        if ip:
            self.display.print("ip: ")
            self.display.set_cursor(0, 8)
            self.display.print(ip)
        else:
            self.display.print("No Internet!")

        self.display.display()
        time.sleep(5)
        self.clear_display()

    def display_resource_usage(self, CPU, Mem_percent, Disk_percent):
        x3 = self.get_bit_text_spacing(CPU)
        x4 = self.get_bit_text_spacing(Mem_percent)
        x5 = self.get_bit_text_spacing(Disk_percent)

        self.display.set_cursor(0, 0)
        self.display.print("CPU:")
        self.display.set_cursor(0, 10)
        self.display.print("Mem:")
        self.display.set_cursor(0, 20)
        self.display.print("Disk:")

        self.display.set_cursor(x3, 0)
        self.display.print(str(CPU.decode('utf-8')))
        self.display.set_cursor(x4, 10)
        self.display.print(str(Mem_percent.decode('utf-8')))
        self.display.set_cursor(x5, 20)
        self.display.print(str(Disk_percent.decode('utf-8')))

        self.display.display()
        time.sleep(2)
        self.clear_display()


if __name__ == '__main__':
    print('starting i2c test')

    monitor = Monitor()
    monitor.init_display()

    while True:
        ip = get_ip_address()
        CPU, Mem_percent, Disk_percent = get_resource_usage()

        monitor.display_ip(ip)
        monitor.display_resource_usage(CPU, Mem_percent, Disk_percent)
