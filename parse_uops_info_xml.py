"""This script parses the uops.info XML file and converts it into JSON that
we can read using the LLVM APIs.
"""

import json
import logging
import subprocess
import tempfile
import sys
import os
import xml.etree.ElementTree as ET

from absl import app
from absl import flags

import xed_xml_utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_path', None,
                    'The path to the uops.info instructions.xml file')

flags.mark_flag_as_required('input_path')


def getOpcodeFromAssembly(assembly):
  with tempfile.TemporaryDirectory() as temp_dir:
    assembly_path = os.path.join(temp_dir, 'assembly.s')
    with open(assembly_path, 'w') as assembly_handle:
      assembly_handle.write(assembly)
    as_command_vector = ['as', assembly_path]
    as_output = subprocess.run(as_command_vector, cwd=temp_dir)
    if as_output.returncode != 0:
      logging.error('Failed to disassemble opcode')
      sys.exit(1)
    output_path = os.path.join(temp_dir, 'a.out')
    get_opcode_command_vector = ['opcode_from_object_file', output_path]
    opcode_output = subprocess.run(
        get_opcode_command_vector,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    if opcode_output.returncode != 0:
      logging.error('Failed to get opcode from object file')
      sys.exit(1)
    return int(opcode_output.stderr.decode('utf-8'))


def main(_):
  tree = ET.parse(FLAGS.input_path)
  logging.info('Finished loading instructions XML file.')
  for child in tree.getroot():
    for instruction_tag in child:
      assembly = xed_xml_utils.instructionNodeToAssembly(instruction_tag)
      print(getOpcodeFromAssembly(assembly))
      break
    break


if __name__ == '__main__':
  app.run(main)
