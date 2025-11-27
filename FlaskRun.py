import subprocess as sp

sp.run(['pip', 'install', '-r', 'requirements.txt'])
sp.run(['python', '-m', 'backend.index'])