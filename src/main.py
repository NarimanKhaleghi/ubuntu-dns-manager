import tkinter as tk
from gui import DNSApp

def main():
    root = tk.Tk()
    # Start logic
    app = DNSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()