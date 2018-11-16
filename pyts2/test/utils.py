import tempfile
import os

def indir(func, dir="."):
    """Do something in dir"""
    def wrapped(*args, **kwargs):
        olddir = os.getcwd()
        os.chdir(dir)
        res = func(*args, **kwargs)
        os.chdir(olddir)
        return res
    return wrapped

def intempdir(func):
    """Makes a temp dir, cd's in, runs func, removes tmp dir, and resets pwd"""
    def wrapped(*args, **kwargs):
        olddir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            res = func(*args, **kwargs)
        os.chdir(olddir)
        return res
    return wrapped

