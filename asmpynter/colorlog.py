
class ColorLog(object):

    _ORIG_HEADER = '\033[1;95m'
    _ORIG_OKBLUE = '\033[94m'
    _ORIG_OKGREEN = '\033[92m'
    _ORIG_WARNING = '\033[93m'
    _ORIG_FAIL = '\033[91m'
    _ORIG_ENDC = '\033[0m'

    def __init__(self):
        self.enable()

    def header(self, st):
        return self.violet(" ** " + st + " ** ")

    def warning(self, st):
        return self.orange(" [*] " + st)

    def fail(self, st):
        return self.red(" [!] " + st)

    def error(self, st):
        return self.fail(st)

    def disabled(self, st):
        return self.orange(" [-] " + st)

    def enabled(self, st):
        return self.blue(" [+] " + st)

    def succeed(self, st):
        return self.green(" [+] " + st)

    def nocinfo(self, st):
        return " [+] " + st

    def info(self, st):
        return self.blue(" [+] " + st)

    def blue(self, st):
        return self.cokblue + st + self.cendc

    def green(self, st):
        return self.cokgreen + st + self.cendc

    def orange(self, st):
        return self.cwarning + st + self.cendc

    def red(self, st):
        return self.cfail + st + self.cendc

    def violet(self, st):
        return self.cheader + st + self.cendc

    def enable(self):
        self.cheader = self._ORIG_HEADER
        self.cokblue = self._ORIG_OKBLUE
        self.cokgreen = self._ORIG_OKGREEN
        self.cwarning = self._ORIG_WARNING
        self.cfail = self._ORIG_FAIL
        self.cendc = self._ORIG_ENDC

    def disable(self):
        self.cheader = ''
        self.cokblue = ''
        self.cokgreen = ''
        self.cwarning = ''
        self.cfail = ''
        self.cendc = ''
