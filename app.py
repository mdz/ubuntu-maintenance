import sys
import os
import subprocess

from flask import Flask, Response
app = Flask(__name__)

@app.route('/')
def unmaintained_packages():
    packages = subprocess.check_output('''dpkg -l | grep '^ii' |  awk ' {print $2}' | xargs apt-cache show | ./grep-dctrl -v -FSupported --exact-match -nsPackage 5y | sort | uniq''', shell=True).split('\n')
    return Response('\n'.join(packages), content_type='text/plain')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
