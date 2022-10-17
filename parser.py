# -*- coding: utf-8 -*-

import os
import sys
import arcpy
import re
import shutil
from io import open

# Processing of .mxd files
def parseMxd(mxd, fo):
  print('Path: %s' % mxd)
  mxdMap = arcpy.mapping.MapDocument(mxd)

  for df in arcpy.mapping.ListDataFrames(mxdMap, "*"):
    fo.write(u'# ' + df.name + u' #\n')
    exit_nesting = 256

    for l in arcpy.mapping.ListLayers(mxdMap, '', df):
      nesting = len(l.longName.split('\\'))
      if nesting > exit_nesting:
        continue
      exit_nesting = 256

      fo.write(''.join([u'\t' for i in range(nesting)]) + l.name)

      if l.supports('DATASOURCE'):
        path = re.match('.*\.\w+', l.dataSource).group(0)
        fo.write(u' -> ' + os.path.relpath(path, sys.argv[0])[3:])
        exit_nesting = nesting

      fo.write(u'\n')
    fo.write(u'\n')

def search_mxd():
  mxdFiles = []
  print('\nSearching .mxd\'s ...')
  for root, dirs, files in os.walk(workdir):
    for file in files:
      if file.endswith(".mxd"):
        mxdFiles.append([root, file])
  print('.mxd: %s found:\n%s\n' % (len(mxdFiles), '\n'.join([f[1] for f in mxdFiles])))

  print('Parsing .mxd\'s ...')
  for rootFile in mxdFiles:
    print('Parsing file: %s ...' % rootFile[1])
    fo = open(os.path.join('PATHS',
        rootFile[1] + '-paths.txt'), 'w', encoding='utf-8')
    path = os.path.join(rootFile[0], rootFile[1])
    fo.write(u'[Проект ' + rootFile[1] + ']' + ' -> ' +
            os.path.relpath(path, sys.argv[0])[3:] + '\n\n')
    parseMxd(path, fo)
    fo.close()


# Processing of .apr files
def parse_section_name(fi):
  section_name = ''

  while True:
    char = fi.read(1)
    if not char or char == '.': break
    section_name += char

  return section_name

def parse_section_text(fi):
  section = ''

  while True:
    char = fi.read(1)
    if not char or char == ')': break
    section += char
  
  return section

def parse_source(fi):
  while True:
    char = fi.read(1)
    if not char: return ''
    if char == '(':
      section_name = parse_section_name(fi)
      if (section_name == 'FN'): return parse_section_text(fi)
      else: parse_section_text(fi)

def parse_apr(apr):
  fi = open(apr, 'r', encoding='windows-1251')
  sections = {}

  while True:
    char = fi.read(1)
    if not char:
      break
    if char == '(':
      section_name = parse_section_name(fi)

      if section_name == 'View':
        section_text = parse_section_text(fi)
        view_name = re.search(r'\tName:\t\"?([\w\d]+)\"?', section_text).group(1)
        for x in re.finditer('\tTheme:\t\"?([\w\d]+)\"?', section_text):
          sections[x.group(1)] = { 'view': view_name }
      
      if section_name.endswith('Theme'):
        section_text = parse_section_text(fi)
        theme_id = re.search(r'(\d+)\n', section_text).group(1)
        section_source = parse_source(fi)
        source_path = re.search(r'\tPath:\t\"(.+)\"', section_source).group(1)
        sections[theme_id]['path'] = source_path
 
  fi.close()

  result = {}
  for k in sections:
    view = sections[k]['view']
    path = sections[k]['path']
    if view not in result:
      result[view] = [path]
    else: result[view].append(path)

  return result

def search_apr():
  aprFiles = {}
  aprFilesIndexes = {}
  for root, dirs, files in os.walk(workdir):
    for file in files:
      if file.endswith('.apr'):
        path = os.path.abspath(os.path.join(root, file))
        if file not in aprFiles:
          aprFilesIndexes[file] = 0
          aprFiles[file] = path
        else:
          aprFilesIndexes[file] += 1
          aprFiles['%s-%s' % (file, aprFilesIndexes[file])] = path      
  print('.apr: %s found:\n%s\n' % (len(aprFiles), '\n'.join(list(aprFiles.values()))))

  print('Parsing .apr\'s ...')
  for file in aprFiles:
    print('Parsing file: ' + aprFiles[file] + ' ...')

    fo = open(os.path.join('PATHS', file + '-paths.txt'), 'w', encoding='windows-1251')
    fo.write(u'[Проект ' + ('%s] -> %s\n' % (file, aprFiles[file])).decode('windows-1251'))

    parsed_data = parse_apr(aprFiles[file])
    for k in parsed_data:
      fo.write('# %s #\n' % k)
      for p in parsed_data[k]:
        fo.write('\t\t%s -> %s\n' % (p.split('/')[-1], p))
    fo.close()


workdir = './'
os.chdir(workdir)
paths = 'PATHS'
if os.path.exists(paths):
  shutil.rmtree(paths)
os.makedirs(paths)

search_mxd()
search_apr()

print('Done!')
