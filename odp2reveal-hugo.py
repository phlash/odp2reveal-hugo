#! /usr/bin/env python3
#
# convert ODP (Open document format presentation) files to reveal-hugo
# compatible markdown. Preserve images, presenter notes and basic format
# of title, lists and links
#
# Author: Phlash
#
# Heavily inspired by AwesomeSlides convert-to-awesome.pl, but in python
#
# Reveal-hugo: https://github.com/dzello/reveal-hugo
# AwesomeSlides: https://github.com/cliffe/AwesomeSlides

import sys
import os
import zipfile
from datetime import datetime, timezone
from functools import reduce
import xml.etree.ElementTree as ET

# How noisy are we?
g_verb = 0
def dbg(l, m):
    if l <= g_verb:
        print(m)

# Namespace dictionary, and mapper to make our parser calls readable..
g_nsdict = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'presentation': 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0',
    'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
    'xlink': 'http://www.w3.org/1999/xlink'
}
def ns_map(tag):
    parts = tag.split(':')
    if len(parts) > 1:
        return '{' + g_nsdict[parts[0]] + '}' + parts[1]
    return parts[0]

# grab all the text from an iteration of xml elements
def get_text(elems):
    txt = ''
    for e in elems:
        txt = reduce(lambda r, t: r+t, e.itertext(), txt)
    return txt

# flatten a hierarchy of text:list/text:list-item to indented text tuples
def flat_list(tlist, indent):
    lst = []
    # starting with a text:list, iterate text:list-item nodes one level down..
    for li in tlist.findall('./text:list-item', g_nsdict):
        # ..and then all child nodes..
        for n in li:
            # if it's another list, recurse into it..
            if n.tag == ns_map('text:list'):
                lst += flat_list(n, indent+1)
            # otherwise grab all the text from it
            else:
                t = reduce(lambda r, t: r+t, n.itertext(), '')
                dbg(2, '{0}: {1}'.format(indent, t))
                lst.append((indent,t))
    return lst

def get_content(frame, parts):
    # what type is this frame?
    frame_class = frame.attrib.get(ns_map('presentation:class'))
    frame_class = frame_class.lower() if frame_class else frame_class
    txt = get_text(frame.findall('./draw:text-box', g_nsdict))
    # ..page title, grab all the text
    if frame_class == 'title':
        parts['title'] = txt
    # ..page outline, build a list of indented text items (bullet-riddled corpse pattern :)
    elif frame_class == 'outline':
        if not 'outline' in parts:
            parts['outline'] = []
        for tbox in frame.findall('./draw:text-box', g_nsdict):
            for tlist in tbox.findall('./text:list', g_nsdict):
                parts['outline'] += flat_list(tlist, 0)
    # ..anything else, check for image or unspecified text
    else:
        img = frame.find('./draw:image', g_nsdict)
        if img:
            if not 'images' in parts:
                parts['images'] = []
            parts['images'].append(img.attrib.get(ns_map('xlink:href')))
        else:
            parts['extra'] = parts['extra'] + txt if 'extra' in parts else txt
    return frame_class

def get_notes(frame):
    # grab all the text from all the draw:text-box items children as a list
    notes = []
    for tbox in frame.findall('./draw:text-box', g_nsdict):
        for n in tbox:
            t = get_text([n])
            dbg(2, 'N: {0}'.format(t))
            notes.append(t)
    return notes

def parse_page(page):
    # build a map of page parts..
    parts = {}
    name = page.attrib.get(ns_map('draw:name'))
    parts['name'] = name
    for frame in page.findall('./draw:frame', g_nsdict):
        frame_class = get_content(frame, parts)
        dbg(2, 'page: {0}: frame {1}'.format(name, frame_class))
    notes = page.find('./presentation:notes', g_nsdict)
    if notes:
        parts['notes'] = []
        for frame in notes.findall('./draw:frame', g_nsdict):
            parts['notes'] += get_notes(frame);
    return parts

def parse(zf):
    pages = []
    for ent in zf.namelist():
        dbg(2, '{0}/zipent: {1}'.format(zf.filename, ent))
    with zf.open('content.xml') as cnt:
        xml = ET.parse(cnt)
    if not xml:
        dbg(0, '{0}: no content.xml found'.format(zf.filename))
        return
    dbg(1, '{0}: loaded content.xml'.format(zf.filename))
    for page in xml.findall('.//draw:page', g_nsdict):
        pages.append(parse_page(page))
    return pages

def out_name(odp, odir):
    base = os.path.basename(odp).rsplit('.')[0]
    return odir + os.sep + base + '.md'

def emit_image(odir, zf, img):
    base = os.path.basename(img)
    ifile = odir + os.sep + base
    with zf.open(img) as zimg:
        with open(ifile, mode='wb') as oimg:
            oimg.write(zimg.read())
    return base

def emit(odir, zf, title, summary, pages):
    os.makedirs(odir, exist_ok=True)
    ofile = out_name(zf.filename, odir)
    with open(ofile, mode='w') as md:
        # write front matter
        if not title:
            title = ofile
        if not summary:
            summary = 'Just another presentation'
        md.write('+++\n')
        md.write('title = "' + title + '"\n')
        md.write('summary = "' + summary + '"\n')
        md.write('date = ' + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+ '\n')
        md.write('layout = "bundle"\n')
        md.write('outputs = ["Reveal"]\n')
        md.write('\n')
        md.write('[reveal_hugo]\n')
        md.write('\ttheme = "moon"\n')
        md.write('\ttransistion = "zoom"\n')
        md.write('\tslide_number = "c/t"\n')
        md.write('\tembedded = true\n')
        md.write('+++\n')
        # write slides..
        pcnt = 0
        for page in pages:
            # separators on all but first slide
            if pcnt:
                md.write('\n\n---\n\n')
            if 'title' in page:
                md.write('\n## ' + page['title'] + '\n')
            if 'outline' in page:
                md.write('\n')
                for line in page['outline']:
                    (indent, text) = (line[0], line[1])
                    md.write(' ')
                    while (indent > 0):
                        indent -= 1
                        md.write('  ')
                    md.write('* ' + text + '\n')
                md.write('\n')
            if 'images' in page:
                for img in page['images']:
                    base = emit_image(odir, zf, img)
                    md.write('\n![](' + base + ')\n')
            if 'extra' in page:
                md.write('\n' + page['extra'] + '\n')
            if 'notes' in page:
                md.write('\n{{% note %}}\n')
                for note in page['notes']:
                    md.write(' * ' + note + '\n')
                md.write('{{% /note %}}\n')
            pcnt = pcnt+1

if __name__ == "__main__":
    odps = []
    odir = '.'
    title = None
    summary = None
    args = iter(sys.argv)
    # skip arg0
    next(args)  
    for arg in args:
        if arg.startswith("-h"):
            print("usage: odp2reveal-hugo [-h] [-v][...] [-o <output dir>] [-t <title>] [-s <summary>] <ODP file> [...]")
            sys.exit(0)
        elif arg.startswith("-v"):
            g_verb = g_verb+1
        elif arg.startswith("-o"):
            odir = next(args)
        elif arg.startswith("-t"):
            title = next(args)
        elif arg.startswith("-s"):
            summary = next(args)
        else:
            odps.append(arg)

    for odp in odps:
        dbg(1, '{0}: opening..'.format(odp))
        with zipfile.ZipFile(odp) as zf:
            emit(odir, zf, title, summary, parse(zf))
