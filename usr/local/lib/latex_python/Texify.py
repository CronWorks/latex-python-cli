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
from imp import load_source
from latex_python.JinjaBase import JinjaTexDocument


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
        filename = realpath(self.arguments['filename'])
        while(True):
            if getmtime(filename) > rebuiltAt:
                rebuiltAt = getmtime(filename)
                self.regenerate(filename)
            if not self.arguments['follow']:
                break
            sleep(SLEEP_SECONDS_BETWEEN_BUILDS)
            self.out.put('sleep timeout reached. checking if file was touched...', self.out.LOG_LEVEL_DEBUG)
            if self.evinceProcess.poll() != None:
                self.out.put('PDF Viewer has closed, or it was already open before running "texify".')
                break


    def regenerate(self, filename):
        (baseFilename, extension) = splitext(texFilename)
        if extension.lower() == '.py':
            pdfFilename = baseFilename + '.pdf'
            documentModule = load_source('documentModule', filename)
            for k in documentModule.__dict__.keys():
                document = documentModule.__dict__[k]  # the convention for Texifiable .py modules
                if isinstance(document, JinjaTexDocument):
                    (errors, warnings, pdfFilename) = document.generate(pdfFilename)  # eventually calls regenerateFromTexFile()
                    break  # only generate the first document we find
        elif extension.lower() == '.tex':
            (errors, warnings, pdfFilename) = generatePdf(filename, self.system, self.arguments['glossary'])

        if errors or warnings:
            self.indentMessages("ERRORS", errors)
            self.indentMessages("WARNINGS", warnings)
        else:
            sleep(1)  # wait for pdf to be written
            self.out.put('starting "evince %s"' % pdfFilename)
            p = self.system.startCommandProcess(['evince', pdfFilename])
            if self.evinceProcess == None:
                self.evinceProcess = p


    def indentMessages(self, label, messages):
        if len(messages) > 0:
            self.out.indent(label + ":")
            for message in messages:
                self.out.put(message)
            self.out.unIndent()

if __name__ == '__main__':
    Texify().run()
