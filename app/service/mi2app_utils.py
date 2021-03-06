"""
mi2app_utils.py

Define utility variables and functions for apps.
"""

# FIXME (likayo): subprocess module in Python 2.7 is not thread-safe.
# Use subprocess32 instead.
import subprocess as sp
import os
import re
import jnius
from jnius import autoclass

ANDROID_SHELL = "/system/bin/sh"

# This one works with Pygame, current bootstrap
PythonService = autoclass('org.renpy.android.PythonService')

# This one works with SDL2
# PythonActivity = autoclass('org.kivy.android.PythonActivity')
# PythonService  = autoclass('org.kivy.android.PythonService')

pyService = PythonService.mService
androidOsBuild = autoclass("android.os.Build")
Context = autoclass('android.content.Context')
File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')
ConnManager = autoclass('android.net.ConnectivityManager')
mWifiManager = pyService.getSystemService(Context.WIFI_SERVICE)


def run_shell_cmd(cmd, wait=False):
    p = sp.Popen(
        "su",
        executable=ANDROID_SHELL,
        shell=True,
        stdin=sp.PIPE,
        stdout=sp.PIPE)
    res, err = p.communicate(cmd + '\n')
    if wait:
        p.wait()
        return res
    else:
        return res


def get_service_context():
    return pyService


def get_cache_dir():
    return str(pyService.getCacheDir().getAbsolutePath())


def get_files_dir():
    return str(pyService.getFilesDir().getAbsolutePath())


def get_phone_manufacturer():
    return androidOsBuild.MANUFACTURER


def get_phone_model():
    return androidOsBuild.MODEL


def get_phone_info():
    cmd = "getprop ro.product.model; getprop ro.product.manufacturer;"
    res = run_shell_cmd(cmd)
    if not res:
        return get_device_id() + '_null-null'
    res = res.split('\n')
    model = res[0].replace(" ", "")
    manufacturer = res[1].replace(" ", "")
    phone_info = get_device_id() + '_' + manufacturer + '-' + model
    return phone_info


def get_operator_info():
    cmd = "getprop gsm.operator.alpha"
    operator = run_shell_cmd(cmd).split('\n')[0].replace(" ", "")
    if operator == '' or operator is None:
        operator = 'null'
    return operator


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    out = run_shell_cmd(cmd)
    tup = re.findall("\'.+\'", out)
    tupnum = re.findall("\d+", "".join(tup))
    deviceId = "".join(tupnum)
    return deviceId


def get_sdcard_path():
    """
    Return the sdcard path of MobileInsight, or None if not accessible
    """
    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED == state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    return sdcard_path


def get_mobileinsight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """

    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED == state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    mobileinsight_path = os.path.join(sdcard_path, "mobileinsight")
    return mobileinsight_path


def get_mobileinsight_log_path():
    """
    Return the log path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "log")


def get_mobileinsight_analysis_path():
    """
    Return the analysis result path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "analysis")


def get_mobileinsight_log_decoded_path():
    """
    Return the decoded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobileinsight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "decoded")


def get_mobileinsight_log_uploaded_path():
    """
    Return the uploaded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobileinsight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "uploaded")


def get_mobileinsight_cfg_path():
    """
    Return the configuration path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "cfg")


def get_mobileinsight_db_path():
    """
    Return the database path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "dbs")


def get_mobileinsight_plugin_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "plugins")


def get_mobileinsight_crash_log_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "crash_logs")


def get_wifi_status():
    return mWifiManager.isWifiEnabled()


def detach_thread():
    try:
        jnius.detach()
    except BaseException:
        pass

def upload_log(filename):
    succeed = False
    form = MultiPartForm()
    form.add_field('file[]', filename)
    form.add_file('file', filename)
    request = urllib2.Request(
        'http://metro.cs.ucla.edu/mobile_insight/upload_file.php')
    request.add_header("Connection", "Keep-Alive")
    request.add_header("ENCTYPE", "multipart/form-data")
    request.add_header('Content-Type', form.get_content_type())
    body = str(form)
    request.add_data(body)

    try:
        response = urllib2.urlopen(request, timeout=3).read()
        if response.startswith("TW9iaWxlSW5zaWdodA==FILE_SUCC") \
                or response.startswith("TW9iaWxlSW5zaWdodA==FILE_EXST"):
            succeed = True
    except urllib2.URLError as e:
        pass
    except socket.timeout as e:
        pass

    if succeed is True:
        try:
            file_base_name = os.path.basename(filename)
            uploaded_file = os.path.join(
                util.get_mobileinsight_log_uploaded_path(), file_base_name)
            # TODO: print to screen
            # print "debug 58, file uploaded has been renamed to %s" % uploaded_file
            # shutil.copyfile(filename, uploaded_file)
            util.run_shell_cmd("cp %s %s" % (filename, uploaded_file))
            os.remove(filename)
        finally:
            util.detach_thread()


class MultiPartForm(object):

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, mimetype=None):
        fupload = open(filename, 'rb')
        body = fupload.read()
        fupload.close()
        if mimetype is None:
            mimetype = mimetypes.guess_type(
                filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        parts = []
        part_boundary = '--' + self.boundary
        parts.extend([part_boundary,
                      'Content-Disposition: form-data; name="%s"; filename="%s"' % (name,
                                                                                    value)] for name,
                     value in self.form_fields)

        parts.extend(
            [
                part_boundary,
                'Content-Disposition: file; name="%s"; filename="%s"' %
                (field_name,
                 filename),
                'Content-Type: %s' %
                content_type,
                '',
                body,
            ] for field_name,
            filename,
            content_type,
            body in self.files)

        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)
