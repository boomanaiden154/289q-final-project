"""
This script contains tooling to parse uiCA JSON to get important parameters,
like the number of (inclusive) cycles between the first and last uop execution
in the first ieration.
"""

import json

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input file from uiCA')

flags.mark_flag_as_required('input_file')


def main(_):
  with open(FLAGS.input_file) as input_file_handle:
    uica_data = json.load(input_file_handle)
  executed_cycle = []
  dispatched_cycle = []
  for cycle_info in uica_data['cycles']:
    if 'executed' in cycle_info:
      for executed_uop in cycle_info['executed']:
        if executed_uop['rnd'] == 0:
          executed_cycle.append(cycle_info['cycle'])
    if 'dispatched' in cycle_info:
      for dispatched_port in cycle_info['dispatched']:
        if cycle_info['dispatched'][dispatched_port]['rnd'] == 0:
          dispatched_cycle.append(cycle_info['cycle'])
  last_cycle = max(executed_cycle)
  if len(dispatched_cycle) != 0:
    first_cycle = min(dispatched_cycle)
  else:
    first_cycle = min(executed_cycle)
  print(last_cycle - first_cycle)


if __name__ == '__main__':
  app.run(main)
