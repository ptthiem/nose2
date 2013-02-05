'''
Patch known Python 2.x interpreters for a bug involving multiprocessing
and modules named __main__.py
'''
import os, sys, subprocess, six

root_install = 'C:\\'
stock_mp_dir = ['lib', 'multiprocessing']
pypy_mp_dir = ['lib-python', '2.7', 'multiprocessing']
patcher_path = r'C:\unix\usr\local\wbin\patch.exe'

interpreters = {
    'pypy 2.0':   os.path.join(root_install, 'pypy-2.0', *pypy_mp_dir),
    'pypy 1.9':   os.path.join(root_install, 'pypy-1.9', *pypy_mp_dir),
    'python 2.6': os.path.join(root_install, 'python26', *stock_mp_dir),
    'python 2.7': os.path.join(root_install, 'python27', *stock_mp_dir),
}

patch = '''--- a/Lib/multiprocessing/forking.py
+++ b/Lib/multiprocessing/forking.py
@@ -459,12 +459,20 @@ def prepare(data):
         process.ORIGINAL_DIR = data['orig_dir']
 
     if 'main_path' in data:
+        # XXX (ncoghlan): The following code makes several bogus
+        # assumptions regarding the relationship between __file__
+        # and a module's real name. See PEP 302 and issue #10845
         main_path = data['main_path']
         main_name = os.path.splitext(os.path.basename(main_path))[0]
         if main_name == '__init__':
             main_name = os.path.basename(os.path.dirname(main_path))
 
-        if main_name != 'ipython':
+        if main_name == '__main__':
+            main_module = sys.modules['__main__']
+            main_module.__file__ = main_path
+        elif main_name != 'ipython':
+            # Main modules not actually called __main__.py may
+            # contain additional code that should still be executed
             import imp
 
             if main_path is None:
'''

if not os.path.isfile(patcher_path):
    print('Patch executable not found')
else:
    print('PATCH.EXE at %s' % patcher_path)

for interpreter in interpreters:
    print("Checking for %s" % interpreter)
    patch_path = interpreters[interpreter]
    print("    Looking for %s" % patch_path)
    if os.path.isdir(patch_path):
        print("    Found target to patch: %s" % patch_path)
        p = subprocess.Popen([patcher_path], cwd=patch_path,
                  shell=True, bufsize=0, stdin=subprocess.PIPE)
        with p.stdin as pipe:
            pipe.write(patch.encode('utf-8'))
        returnvalue = p.wait()
        print('Patch Returned: %i' % returnvalue)
    else:
        print("    Skipping %s" % interpreter)


