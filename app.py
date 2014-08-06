import os
import subprocess
import datetime
from dateutil.relativedelta import relativedelta
import json

from flask import Flask, Response
app = Flask(__name__)
app.debug = True

def ubuntu_release():
    release = None
    try:
        release = subprocess.check_output(['lsb_release','-rs']).strip()
    except:
        with open('/etc/lsb-release') as f:
            for line in f:
                k, v = line.split('=')
                if k == 'DISTRIB_RELEASE':
                    release = v
                    break
            if not release:
                raise 'Failed to determine which Ubuntu release this is'

    print "Ubuntu release: %s" % release
    return release

def ubuntu_release_date(version_number):
    year, month = map(int,version_number.split('.'))
    # support periods are only accurate to the month anyway
    dt = datetime.datetime(year=2000+year,month=month,day=1)
    print "Ubuntu release date: %s" % dt
    return dt

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

def package_maintenance_status():
    now = datetime.datetime.now()
    release_date = ubuntu_release_date(ubuntu_release())
    package_status = {}
    for package, support_period in get_package_maintenance_periods().items():
        if support_period is None:
            package_status[package] = 'Unknown'
        elif release_date + support_period < now:
            #print "Lapsed: %s > %s" % (release_date+support_period, now)
            package_status[package] = 'Lapsed'
        else:
            package_status[package] = 'OK'

    return package_status

@app.route('/json')
def as_json():
    return Response(json.dumps(package_maintenance_status()), content_type='application/json')

@app.route('/')
def as_text():
    response = ''
    for package, status in sorted(package_maintenance_status().items(), key=lambda x: x[1]):
        response += '%s: %s\n' % (package, status)

    return Response(response, content_type='text/plain')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        print as_text().get_data()
