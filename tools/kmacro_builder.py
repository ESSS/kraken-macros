import os
import shutil
import sys


def copy_macro_files(macro_filename):
    src = os.path.dirname(macro_filename)
    dst = get_macros_dirname()
    for name in os.listdir(src):
        fullname = os.path.join(src, name)
        if os.path.isfile(fullname):
            shutil.copy2(fullname, dst)
        else:
            dst_dirname = os.path.join(dst, name)
            if os.path.isdir(dst_dirname):
                shutil.rmtree(dst_dirname)
            shutil.copytree(fullname, dst_dirname, ignore=shutil.ignore_patterns("*.pyc"))    
    
    
def get_macros_dirname():
    if sys.platform == 'win32':
        return os.path.expanduser("~/Documents/Kraken/Scripts/")
    else:
        return os.path.expanduser("~/.kraken20/scripts/")


def main(args):
    macro_filename = os.path.abspath(args[1])
    if not os.path.split(macro_filename)[1].startswith("macro_"):
        sys.stderr.write("Error: selected file is not a Kraken Macro")
        exit(1)
    copy_macro_files(macro_filename)
    _, macro_basename = os.path.split(macro_filename)
    print(f"{macro_basename} and dependencies copied to Scripts folder")


if __name__ == '__main__':
    main(sys.argv)