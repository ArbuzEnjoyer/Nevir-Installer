import PyInstaller.__main__
from pathlib import Path

current_dir = Path(__file__).parent
icon_path = str(current_dir / 'icon.ico')

PyInstaller.__main__.run([
    'installer.py',
    '--onefile',
    '--noconsole',
    f'--icon={icon_path}',
    '--clean',
    '--name=Nevir Installer',
    '--add-data=icon.ico;.',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=ttkthemes',
    '--collect-all=ttkthemes',
    '--collect-all=PIL',
    '--collect-all=requests',
    '--collect-all=psutil',
]) 
