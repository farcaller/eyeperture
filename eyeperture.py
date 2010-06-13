#!/usr/bin/env python
# Copyright (c) 2010 Vladimir "Farcaller" Pouzanov <farcaller@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys, os
from datetime import datetime
import optparse
try:
    from appscript import *
except ImportError:
    print >>sys.stderr, "You need to install \"appscript\" bridge, sudo easy_install appscript should work."
    sys.exit(1)

class EyePerture(object):
    IMPORT_FOLDER_NAME = u'Eye-Fi Import'
    
    def __init__(self, fldname=None):
        self.ap = app('Aperture')
        if fldname:
            self.fldname = fldname
        else:
            self.fldname = self.IMPORT_FOLDER_NAME
    
    def library(self):
        assert(len(self.ap.libraries()) == 1)
        return self.ap.libraries[0]()
    
    def __make(self, kind, opts, root=None):
        if not root:
            root = self.library()
        root.make(new=kind, with_properties=opts)
    
    def get_import_folder(self):
        ex = self.library().folders[self.fldname].exists()
        fld = None
        if not ex:
            print "[EP] creating %s folder" % (self.fldname, )
            self.__make(k.folder, {k.name: self.fldname})
        fld = self.library().folders[self.fldname]()
        if str(fld.parent()).find('ScriptingTrash') != -1:
            print "[EP] restoring %s from trash (and trashing contents!)" % (self.fldname, )
            fld.parent().restore(fld)
            for cnt in fld.containers():
                cnt.delete()
        return fld
    
    def get_import_project(self, projname=None, fld=None):
        if not fld:
            fld = self.get_import_folder()
        if not projname:
            projname = datetime.now().strftime('%F')
        ex = fld.projects[unicode(projname)].exists()
        if not ex:
            print "[EP] creating %s project in %s folder" % (projname, self.fldname, )
            self.__make(k.project, {k.name: unicode(projname), k.parent: fld}, fld)
        proj = fld.projects[unicode(projname)]
        return proj
    
    def __alias_files(self, files):
        l = []
        for i in files:
            l.append(mactypes.Alias(i))
        return l
    
    def import_files_to_project(self, files, proj=None, meth=k.copying):
        if not proj:
            proj = self.get_import_project()
        self.ap.import_(self.__alias_files(files), by=meth, into=proj, timeout=600)
    

if __name__ == '__main__':
    parser = optparse.OptionParser(
        usage="Usage: %s [-f FOLDER] [-p PROJECT] [-c|-m|-r] FILES ..." % (sys.argv[0], ),
        description="Aperture images importer",
        version='0.3')
    parser.add_option('-f', '--folder', action='store', type='string', dest='folder',
        help=("Target folder name, default: %s" % (EyePerture.IMPORT_FOLDER_NAME,)) )
    parser.add_option('-p', '--project', action='store', type='string', dest='project',
        help="Target project name inside folder, default: YYYY-MM-DD")
    
    g = optparse.OptionGroup(parser, "Import method")
    g.add_option('-c', '--copying', action='store_const', const=k.copying, dest='method',
        help="Import by copying (default)", default=k.copying)
    g.add_option('-m', '--moving', action='store_const', const=k.moving, dest='method',
        help="Import by moving")
    g.add_option('-r', '--referencing', action='store_const', const=k.referencing, dest='method',
        help="Import by referencing")
    parser.add_option_group(g)
    
    options, args = parser.parse_args()
    
    if options.folder:
        ep = EyePerture(options.folder)
    else:
        ep = EyePerture()
    
    if options.project:
        pj = ep.get_import_project(options.project)
    else:
        pj = ep.get_import_project()
    
    l = []
    for fn in args:
        if os.path.isfile(fn):
            l.append(fn)
        else:
            print "[EP] not a file: %s" % (fn,)
    if len(l) == 0:
        #print >>sys.stderr, "You have to specify at least one file to import"
        parser.parse_args(['-h'])
        sys.exit(2)
    
    ep.import_files_to_project(l, pj, options.method)
