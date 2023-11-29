# Display.py
from tkinter import *
import threading


class Display:
    def __init__(self):
        self.root = Tk()
        self.current_board_label = None
        self.connected_label = None
        self.command_to_send = None
        self.inputtxt = ""
        self.Chat = None
        self.Display = None
        self.display_text = ""

    def start_gui(self):
        self.root.geometry("400x400")
        self.root.title(" Bulletin Board ")
        self.current_board_label = Label(text="Current Board: None")
        self.connected_label = Label(text="Connected: False")
        self.inputtxt = Text(self.root, height=5,
                             width=40,
                             bg="light yellow")
        self.Chat = Text(self.root, height=15,
                         width=40,
                         bg="light cyan")
        self.Display = Button(self.root, height=2,
                              width=20,
                              text="Send",
                              command=lambda: self.set_command_to_send())
        self.display_text = ""

        self.current_board_label.pack()
        self.connected_label.pack()
        self.inputtxt.pack()
        self.Display.pack()
        self.Chat.pack()
        mainloop()
