import threading
from tkinter import *
import serial


class MainWindow:
    def __init__(self):
        self.root = Tk()
        self.root.title('MailHome')
        self.root.geometry('1080x720')
        self.input = Text(self.root, font="Arial 30")
        self.output = Text(self.root, font="Arial 30")
        self.log = Text(self.root, font="Arial 30")
        self.input.place(width=360, height=620, x=0, y=100)
        self.output.place(width=360, height=620, x=360, y=100)
        self.log.place(width=360, height=620, x=720, y=100)
        self.input_label = Label(self.root, text="Sender", anchor="center", font="Arial 30")
        self.output_label = Label(self.root, text="Recipient", anchor="center", font="Arial 30")
        self.log_label = Label(self.root, text="Logs", anchor="center", font="Arial 30")
        self.input_label.place(width=360, height=100, x=0, y=0)
        self.output_label.place(width=360, height=100, x=360, y=0)
        self.log_label.place(width=360, height=100, x=720, y=0)
        self.output.config(state='disabled')
        self.log.config(state='disabled')
        self.input.bind("<KeyRelease>", self.on_button_clicked)
        self.port1 = serial.Serial()
        self.port2 = serial.Serial()
        try:
            self.port1 = serial.Serial('COM2', 115200)
            self.port2 = serial.Serial('COM3', 115200)
            self.make_log('Port is open')
        except serial.SerialException:
            self.make_log("Can't open ports")

    """First Com"""
    def on_button_clicked(self, event):
        if event.keycode == 8:
            self.send_data('\b')
        else:
            self.send_data(self.input.get(1.0, END + '-1c')[-1])

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
                self.output.config(state='normal')
                try:
                    out = self.port2.read().decode('cp1251')
                except serial.PortNotOpenError:
                    self.make_log('Ports are closed')
            if out == '\b':
                self.output.delete("end-2c")
            else:
                self.output.insert(END, out)
            self.output.config(state='disabled')

    """Logs"""
    def make_log(self, message):
        self.log.config(state='normal')
        self.log.insert(END, message + '\n')
        self.log.config(state='disabled')


if __name__ == "__main__":
    app = MainWindow()
    tr_in = threading.Thread(target=app.read_data)
    tr_in.daemon = True
    tr_in.start()
    app.root.mainloop()
