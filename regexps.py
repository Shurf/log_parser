import re


class RegexCollection:
    @staticmethod
    def get_regex_collection_copy():
        return sorted([re() for re in BaseRegWrapper.__subclasses__()], key=lambda reg: reg.is_final)


# Classes For Regular expressions to parse lines in log ########
class BaseRegWrapper(object):
    def __init__(self, regexp, is_final=False):
        self.regexp = regexp
        self.compiled_regex = re.compile(self.regexp)
        self.re_m = None
        self.is_final = is_final

    def match(self, string):
        # self.re_m = re.search(self.regexp, string)
        self.re_m = self.compiled_regex.search(string)
        return self.re_m

    @property
    def subtype(self):
        try:
            if self.re_m is None:
                x = 5
            return self.re_m.group(1)
        except IndexError:
            return ""

    def __str__(self):
        return self.regexp


class OkReg(BaseRegWrapper):
    def __init__(self):
        super(OkReg, self).__init__('\-\ Ok\s*$', is_final=True)
        self.diagnose = 'clear'


class IncurableReg(BaseRegWrapper):
    def __init__(self):
        super(IncurableReg, self).__init__('incurable')
        self.diagnose = 'incurable'


class DecompressionErrorReg(BaseRegWrapper):
    def __init__(self):
        super(DecompressionErrorReg, self).__init__('decompression\ error')
        self.diagnose = 'decompression error'


class HeaderCRCErrorReg(BaseRegWrapper):
    def __init__(self):
        super(HeaderCRCErrorReg, self).__init__('header CRC error')
        self.diagnose = 'header CRC error'


class TooDeepReg(BaseRegWrapper):
    def __init__(self):
        super(TooDeepReg, self).__init__('too deep\s*$', is_final=True)
        self.diagnose = 'too deep'


class UnpackErrorReg(BaseRegWrapper):
    def __init__(self):
        super(UnpackErrorReg, self).__init__('unpack\ error')
        self.diagnose = 'unpack error'


class PasswordProtectedReg(BaseRegWrapper):
    def __init__(self):
        super(PasswordProtectedReg, self).__init__('password protected\s*$', is_final=True)
        self.diagnose = 'password protected'


class ReadErrorReg(BaseRegWrapper):
    def __init__(self):
        super(ReadErrorReg, self).__init__('read error\s*$', is_final=True)
        self.diagnose = 'read error'


class PackedByReg(BaseRegWrapper):
    def __init__(self):
        super(PackedByReg, self).__init__(' packed by (.+)$', is_final=True)
        self.diagnose = 'packed by'


class IsArchiveReg(BaseRegWrapper):
    def __init__(self):
        super(IsArchiveReg, self).__init__(' is (.+) archive\s*$', is_final=True)
        self.diagnose = 'archive'


class IsContainerReg(BaseRegWrapper):
    def __init__(self):
        super(IsContainerReg, self).__init__(' is (.+) container\s*$', is_final=True)
        self.diagnose = 'container'


class InfectedReg(BaseRegWrapper):
    def __init__(self):
        # super(InfectedReg, self).__init__(' infected(\s[^w]|\s*$|,).*')
        super(InfectedReg, self).__init__(' infected(\s[^w]|\s*$|,)')
        self.diagnose = 'infected'


class InfectedWithReg(BaseRegWrapper):
    def __init__(self):
        super(InfectedWithReg, self).__init__(' infected with (.+)$', is_final=True)
        self.diagnose = 'infected'


class MalwareProgrammReg(BaseRegWrapper):
    '''
    Hacktools, dialers, jokes and etc
    '''

    def __init__(self):
        super(MalwareProgrammReg, self).__init__(' is .+ program (.+)$', is_final=True)
        self.diagnose = 'malware'


"""class PackedByReg(BaseRegWrapper):
    def __init__(self):
        super(PackedByReg, self).__init__('^.+ packed by (.+)$')
        self.diagnose = 'packed by'


class IsArchiveReg(BaseRegWrapper):
    def __init__(self):
        super(IsArchiveReg, self).__init__('^.+ is (.+) archive\s*$')
        self.diagnose = 'archive'


class IsContainerReg(BaseRegWrapper):
    def __init__(self):
        super(IsContainerReg, self).__init__('^.+ is (.+) container\s*$')
        self.diagnose = 'container'


class InfectedReg(BaseRegWrapper):
    def __init__(self):
        super(InfectedReg, self).__init__('^.+ infected(\s[^w]|\s*$|,).*')
        self.diagnose = 'infected'


class InfectedWithReg(BaseRegWrapper):
    def __init__(self):
        super(InfectedWithReg, self).__init__('^.+ infected with (.+)$')
        self.diagnose = 'infected'


class MalwareProgrammReg(BaseRegWrapper):
    '''
    Hacktools, dialers, jokes and etc
    '''
    def __init__(self):
        super(MalwareProgrammReg, self).__init__('^.+ is .+ program (.+)$')
        self.diagnose = 'malware'"""


# End of Classes for Regular Expressions ##########
