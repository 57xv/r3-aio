try:
    import sys
    import os

    def OpenSites():
        try:
            import webbrowser
            from Program.Config.Config import telegram, gunslol
            webbrowser.open(f'https://{gunslol}')
        except: pass

    if sys.platform.startswith("win"):
        os.system("cls")
        print("Installing the python modules required for r3aio:\n")
        os.system("python -m pip install --upgrade pip")
        os.system("python -m pip install -r requirements.txt")
        OpenSites()
        os.system("python main.py")

    elif sys.platform.startswith("linux"):
        os.system("clear")
        print("Installing the python modules required for r3aio:\n")
        os.system("pip3 install --upgrade pip")
        os.system("pip3 install -r requirements.txt")
        OpenSites()
        os.system("python3 main.py")

except Exception as e:
    input(e)