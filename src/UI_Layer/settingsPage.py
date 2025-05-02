from tkinter import Tk, ttk
import tkinter as tk

class settings_page_base(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text='Settings Page', font=('Helvetica', 16))
        label.pack(pady=20)
    
    def deselect(self):
        pass