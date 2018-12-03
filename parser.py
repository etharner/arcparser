# -*- coding: utf-8 -*-

import os
import sys
import arcpy
import re
import shutil
from io import open


def parseMxd(mxd):
  print 'Path: ' + mxd
  mxdMap = arcpy.mapping.MapDocument(mxd)

  for df in arcpy.mapping.ListDataFrames(mxdMap, "*"):
    f.write(u'# ' + df.name + u' #\n')
    exit_nesting = 256

    for l in arcpy.mapping.ListLayers(mxdMap, '', df):
      nesting = len(l.longName.split('\\'))
      if nesting > exit_nesting:
        continue
      exit_nesting = 256

      f.write(''.join([u'\t' for i in range(nesting)]) + l.name)

      if l.supports('DATASOURCE'):
        path = re.match('.*\.\w+', l.dataSource).group(0)
        f.write(u' -> ' + os.path.relpath(path, sys.argv[0])[3:])
        exit_nesting = nesting

      f.write(u'\n')
    f.write(u'\n')


workdir = os.path.dirname(sys.argv[0])
os.chdir(workdir)
paths = 'PATHS'
if os.path.exists(paths):
  shutil.rmtree(paths)
os.makedirs(paths)

mxdFiles = []
print 'Searching .mxd\'s ...\n'
for root, dirs, files in os.walk(workdir):
  for file in files:
    if file.endswith(".mxd"):
      mxdFiles.append([root, file])
print str(len(mxdFiles)) + ' found:\n[' + ', '.join([f[1] for f in mxdFiles]) + ']\n'

print 'Parsing .mxd\'s ...\n'
for rootFile in mxdFiles:
  print 'Parsing file: ' + rootFile[1] + ' ...'
  f = open(os.path.join('PATHS', os.path.splitext(
      rootFile[1])[0] + '-paths.txt'), 'w', encoding='utf-8')
  path = os.path.join(rootFile[0], rootFile[1])
  f.write(u'[Проект ' + rootFile[1] + ']' + ' -> ' +
          os.path.relpath(path, sys.argv[0])[3:] + '\n\n')
  parseMxd(path)

print 'Done!'
