import os
import subprocess
import datetime
from dateutil.relativedelta import relativedelta
import json

from flask import Flask, Response
app = Flask(__name__)
app.debug = True

def ubuntu_release():
    return subprocess.check_output(['lsb_release','-rs']).strip()

def ubuntu_release_date(version_number):
    year, month = map(int,version_number.split('.'))
    # support periods are only accurate to the month anyway
    return datetime.datetime(year=year,month=month,day=1)

def support_period_text_to_relativedelta(text):
    if text is None: return None

    unit = text[-1]
    value = int(text[:-1])
    if unit == 'y':
        return relativedelta(years=value)
    elif unit == 'm':
        return relativedelta(months=value)
    else:
        raise 'Unknown unit: "%s"' % unit

@app.route('/test')
def get_package_maintenance_periods():
    output = subprocess.check_output('''dpkg -l | grep '^ii' |  awk ' {print $2}' | sort | uniq | xargs apt-cache show | ./grep-dctrl -sPackage,Supported '' ''', shell=True)

    supported = {}
    for paragraph in output.split('\n\n'):
        fields = {}
        for line in paragraph.split('\n'):
            if not line.strip(): continue
            k, v = map(str.strip, line.split(':'))
            fields[k.capitalize()] = v
        if 'Package' in fields:
            support_period = support_period_text_to_relativedelta(fields.get('Supported', None))
            supported[fields['Package']] = support_period
        else:
            # XXX - malformed paragraph
            pass
    return supported

@app.route('/')
def unmaintained_packages():
    now = datetime.datetime.now()
    release_date = ubuntu_release_date(ubuntu_release())
    package_status = {}
    for package, support_period in get_package_maintenance_periods().items():
        if support_period is None:
            package_status[package] = 'Unknown'
        elif release_date + support_period > now:
            package_status[package] = 'Lapsed'
        else:
            package_status[package] = 'OK'

    return Response(json.dumps(package_status), content_type='application/json')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
