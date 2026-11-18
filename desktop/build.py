"""One-file program for the computer this runs on: python desktop/build.py (Windows: .exe; Linux: run it in Linux, e.g. WSL).
Needs pygame-ce and pyinstaller (and tkinter, for the ROM dialog). The ROM is not packed: the game asks for it.
Out: desktop/dist/ElectronicDetective[.exe]."""
import os, sys
import PyInstaller.__main__

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(here, '..')
fonts = '/usr/share/fonts/truetype/dejavu'           # Linux may have no Arial; Windows uses its own
data = [a for f in ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf') if os.path.exists(os.path.join(fonts, f))
        for a in ('--add-data', os.path.join(fonts, f) + os.pathsep + '.')]
PyInstaller.__main__.run([
    os.path.join(here, 'entry.py'), '--onefile', '--windowed', '--name', 'ElectronicDetective', '--noconfirm',
    '--paths', os.path.join(root, 'game'), '--paths', os.path.join(root, 'research', 'solver'),
    '--hidden-import', 'par', '--hidden-import', 'solver',
    '--distpath', os.path.join(here, 'dist'), '--workpath', os.path.join(here, 'work'), '--specpath', os.path.join(here, 'work'),
    *data])
