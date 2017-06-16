import re


class LineParser:
    @staticmethod
    def get_file_path(line):
        reg = re.search('([a-f0-9]{40}[^\"]*)', line)
        if not reg:
            print("Can`t find hash in line {}".format(line))
            return None
        return reg.group(1)

    @staticmethod
    def get_file_diagnose(line):
        reg = re.search('[^\"]*\"[^\"]*\"(.*)', line)
        if not reg:
            print("Can`t find hash in line {}".format(line))
            return None
        return reg.group(1)
