#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version. 

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import argparse
from os.path import getmtime, realpath, splitext
from shutil import copyfile
from subprocess import STDOUT
from time import sleep
from latex_python.XetexWrapper import generatePdf
from py_base.Job import Job

SLEEP_SECONDS_BETWEEN_BUILDS = 1

class Texify(Job):
    'Generate a PDF file from a LaTeX or PyTeX template.'
    evinceProcess = None

    def defineCustomArguments(self, parser):
        parser.add_argument('-f',
                            '--follow',
                            action='store_true',
                            help='follow changes to .tex file and rebuild automatically')
        parser.add_argument('-g',
                            '--glossary',
                            action='store_true',
                            help='run the glossary creation tool')
        parser.add_argument('filename',
                            metavar='<filename>',
                            help='filename of the .tex file to process (may include embedded Python)')

    def run(self):
        rebuiltAt = 0
        self.texFilename = realpath(self.arguments['filename'])
        while(True):
            if getmtime(self.texFilename) > rebuiltAt:
                rebuiltAt = getmtime(self.texFilename)
                self.regenerate()
            if not self.arguments['follow']:
                break
            sleep(SLEEP_SECONDS_BETWEEN_BUILDS)
            if self.evinceProcess.poll() != None:
                self.out.put('PDF Viewer has closed, or it was already open before running "texify".')
                break


    def regenerate(self):
        generatePdf(self.texFilename, self.system, self.arguments['glossary'])
        texFilePieces = splitext(self.texFilename)
        p = self.system.startCommandProcess(['evince', texFilePieces[0] + '.pdf'])
        if self.evinceProcess == None:
            self.evinceProcess = p

if __name__ == '__main__':
    Texify().run()
