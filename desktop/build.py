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
icon = os.path.join(root, 'game', 'icon.png')         # the window's icon; Windows also puts it on the .exe (needs Pillow)
data += ['--add-data', icon + os.pathsep + '.'] + (['--icon', icon] if os.name == 'nt' else [])
PyInstaller.__main__.run([
    os.path.join(here, 'entry.py'), '--onefile', '--windowed', '--name', 'ElectronicDetective', '--noconfirm',
    '--paths', os.path.join(root, 'game'), '--paths', os.path.join(root, 'research', 'solver'),
    '--hidden-import', 'par', '--hidden-import', 'solver',
    '--distpath', os.path.join(here, 'dist'), '--workpath', os.path.join(here, 'work'), '--specpath', os.path.join(here, 'work'),
    *data])

# self-check: the built program, started as its own solver, gives the par that par.py gives for the same case
import json, random, subprocess
sys.path[:0] = [os.path.join(root, 'game'), os.path.join(root, 'research', 'solver')]
import par, rules
case = rules.deal(random.Random(5))
want = str(par.case_par(case, 2))
exe = os.path.join(here, 'dist', 'ElectronicDetective' + ('.exe' if os.name == 'nt' else ''))
got = subprocess.run([exe, 'case', json.dumps(case), '2'], capture_output=True, text=True, timeout=300).stdout.strip()
assert got == want, 'the built program gives par %r, par.py gives %r' % (got, want)
print('self-check OK: the built program counts par like par.py (%s)' % got)
