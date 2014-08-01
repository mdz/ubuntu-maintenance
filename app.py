import sys
import os
import subprocess

from flask import Flask
app = Flask(__name__)

@app.route('/')
def show_unmaintained_packages():
    packages = subprocess.check_output('''dpkg -l | grep '^ii' |  awk ' {print $2}' | xargs apt-cache show | grep-dctrl -v -FSupported --exact-match -nsPackage 5y''', shell=True).split('\n')
    for package in packages:
        if package:
            print package

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
