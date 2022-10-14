import threading
import random
from tkinter import *
import serial

# Для проверки можете использовать сайт https://crccalc.com/
# Пример ввода: 7e0ae4a112233445566778897665 (Ввод только маленькими буквами и только hex)
DATA_LENGTH_DEC = 10 * 2  # Длинна строки (*2 Потому что hex число записывается в 2 символа)
DATA_LENGTH_HEX_STRING = str(hex(int(DATA_LENGTH_DEC / 2)))[2:].rjust(2, '0')  # Переводим в hex отбрасывая при этом 0x
PACKET_LENGTH_DEC_STRING = DATA_LENGTH_DEC + 4 * 2  # 4 байта на флаги (2 потому что hex число записывается в 2 символа)
FLAG_HEX_STRING = '7e'  # Флаг начала пакета
FLAG_BIN_STRING = str(bin(int(FLAG_HEX_STRING, 16)))[2:]  # Переводим в bin отбрасывая при этом 0b
RANDOM_LIST = tuple(map(str, range(0, 10))) + tuple(map(chr, range(97, 103)))


def check_packet(packet: str) -> bool:
    try:
        hex(int(packet[0:PACKET_LENGTH_DEC_STRING], 16))
    except ValueError:
        app.make_log("The entered package does not consist of hexadecimal")
        return False
    if len(packet) != PACKET_LENGTH_DEC_STRING:
        app.make_log("Packet length not correct")
        return False
    if packet[0:2] != FLAG_HEX_STRING:  # Packet start flag
        app.make_log("Invalid packet start flag")
        return False
    if packet[2:4] != DATA_LENGTH_HEX_STRING:  # Data length
        app.make_log("Bad flag length")
        return False
    if packet[4:6]:  # Source Address
        pass
    if packet[6:8]:  # Destination Address
        pass
    if packet[8:DATA_LENGTH_DEC]:  # Data
        pass
    return True


def crc16_generator(data: str, poly: hex = 0xA001):
    crc = 0xFFFF
    for i in range(0, len(data), 2):
        crc ^= int(data[i:i + 2], 16)
        for _ in range(8):
            crc = ((crc >> 1) ^ poly if (crc & 0x0001) else crc >> 1)
    return hex(crc)[2:].rjust(4, '0')  # Контрольная сумма должна быть 2 байта т.е. 4 символа


def make_thread_for_reader():
    tr_in = threading.Thread(target=app.read_data)
    tr_in.daemon = True
    tr_in.start()


def break_package(packet: str, nums_of_corrupted: int) -> str:
    packet = list(packet)
    for i in range(nums_of_corrupted):
        packet[8 + i] = RANDOM_LIST[random.randint(0, len(RANDOM_LIST) - 1)]
    packet = ''.join(packet)
    app.package_when_sending_textbox.config(state='normal')
    app.package_when_sending_textbox.insert(END, packet[:8])
    app.package_when_sending_textbox.insert(END, packet[8:8 + nums_of_corrupted], 'tag_red_text')
    app.package_when_sending_textbox.insert(END, packet[8 + nums_of_corrupted:] + '\n')
    app.package_when_sending_textbox.config(state='disabled')
    return packet


class MainWindow:
    def __init__(self):
        self.root = Tk()
        self.root.title('MailHome')
        self.root.geometry('1440x820')
        self.input_textbox = Text(self.root, font="Arial 10")
        self.output_textbox = Text(self.root, font="Arial 10")
        self.log_textbox = Text(self.root, font="Arial 10")
        self.package_when_sending_textbox = Text(self.root, font="Arial 10")
        self.input_textbox.place(width=360, height=620, x=0, y=100)
        self.package_when_sending_textbox.place(width=360, height=620, x=360, y=100)
        self.output_textbox.place(width=360, height=620, x=720, y=100)
        self.log_textbox.place(width=360, height=620, x=1080, y=100)
        self.input_label = Label(self.root, text="Sender", anchor="center", font="Arial 30")
        self.package_when_sending_label = Label(self.root, text="Package", anchor="center", font="Arial 30")
        self.output_label = Label(self.root, text="Recipient", anchor="center", font="Arial 30")
        self.log_label = Label(self.root, text="Logs", anchor="center", font="Arial 30")
        self.input_label.place(width=360, height=100, x=0, y=0)
        self.package_when_sending_label.place(width=360, height=100, x=360, y=0)
        self.output_label.place(width=360, height=100, x=720, y=0)
        self.log_label.place(width=360, height=100, x=1080, y=0)
        self.output_textbox.config(state='disabled')
        self.log_textbox.config(state='disabled')
        self.package_when_sending_textbox.config(state='disabled')
        self.send_button = Button(text="Send", command=self.send_button_click, font="Arial 30")
        self.send_button.place(width=720, height=100, x=0, y=720)
        self.clear_button = Button(text="Clear", command=self.clear_button_click, font="Arial 30")
        self.clear_button.place(width=720, height=100, x=720, y=720)
        self.spinbox_var = StringVar(value='0')
        self.spinbox = Spinbox(from_=0, to=DATA_LENGTH_DEC, textvariable=self.spinbox_var, state='readonly')
        self.spinbox.place(width=100, height=25, x=150, y=0)
        self.corrupted_label = Label(self.root, text="Number of corrupted bytes", anchor="center", font="Arial 8")
        self.corrupted_label.place(width=150, height=25, x=0, y=0)
        self.package_when_sending_textbox.tag_config('tag_red_text', foreground='red')
        self.input_textbox.bind("<KeyRelease>", self.on_button_clicked)
        self.data_last_poss = 0
        self.counter = 0
        self.port1 = serial.Serial()
        self.port2 = serial.Serial()
        try:
            self.port1 = serial.Serial('COM2', 115200)
            self.port2 = serial.Serial('COM3', 115200)
            self.make_log('Ports are open')
        except serial.SerialException:
            self.make_log("Can't open ports")

    """First Com"""

    def on_button_clicked(self, event):
        if event.keycode == 8:
            if self.counter != 0:
                self.counter -= 1
        elif self.counter != PACKET_LENGTH_DEC_STRING:
            self.counter += 1
            if self.counter == PACKET_LENGTH_DEC_STRING:
                self.make_log("Maximum package length reached")
                self.input_textbox.config(state='disabled')
        print(self.counter)

    def send_button_click(self):
        self.input_textbox.config(state='normal')
        data = self.input_textbox.get(1.0, END)
        packet = data[self.data_last_poss:len(data) - 1]
        if check_packet(packet):
            checksum = crc16_generator(packet)
            self.make_log("Sender's checksum = " + checksum)
            packet += checksum
            try:
                nums_of_corrupted = int(self.spinbox.get())
            except ValueError:
                app.make_log("The number of corrupted bytes is not integer")
                self.data_last_poss = len(data)
                self.input_textbox.insert(END, '\n')
                self.counter = 0
                return
            packet = break_package(packet, nums_of_corrupted)
            self.send_data(packet)
        self.data_last_poss = len(data)
        self.input_textbox.insert(END, '\n')
        self.counter = 0

    def send_data(self, data):
        try:
            self.port1.write(data.encode('cp1251'))
        except serial.PortNotOpenError:
            self.make_log('Ports are closed')

    """Second Com"""

    def read_data(self):
        out = ''
        while 1:
            while self.port2.inWaiting() > 0:
                self.output_textbox.config(state='normal')
                try:
                    out += self.port2.read().decode('cp1251')
                except serial.PortNotOpenError:
                    self.make_log('Ports are closed')
            if out != '':
                out_check_sum = crc16_generator(out[0:PACKET_LENGTH_DEC_STRING])
                if out_check_sum != out[PACKET_LENGTH_DEC_STRING:]:
                    self.make_log("Transmission error: sender and receiver checksums are not equal. Recipient "
                                  "checksum = " + out_check_sum)
                else:
                    self.make_log("Recipient checksum = " + out_check_sum)
                    self.output_textbox.insert(END, out[0:PACKET_LENGTH_DEC_STRING] + '\n')
                out = ''
                self.output_textbox.config(state='disabled')

    """Logs"""

    def make_log(self, message):
        self.log_textbox.config(state='normal')
        self.log_textbox.insert(END, message + '\n')
        self.log_textbox.config(state='disabled')

    """Clear fields"""

    def clear_button_click(self):
        self.input_textbox.config(state='normal')
        self.output_textbox.config(state='normal')
        self.package_when_sending_textbox.config(state='normal')
        self.input_textbox.delete(1.0, END)
        self.output_textbox.delete(1.0, END)
        self.package_when_sending_textbox.delete(1.0, END)
        self.output_textbox.config(state='disabled')
        self.package_when_sending_textbox.config(state='disabled')
        self.data_last_poss = 0
        self.counter = 0
        self.make_log("Screen is cleared")


if __name__ == "__main__":
    app = MainWindow()
    make_thread_for_reader()
    app.root.mainloop()
