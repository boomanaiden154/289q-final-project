"""
A tool that produces ASCII art for a uop schedule.
"""

import json

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The path to the input file.')

flags.mark_flag_as_required('input_file')


def main(_):
  with open(FLAGS.input_file) as input_file_handle:
    scheduled_uops = json.load(input_file_handle)

  scheduled_uops = sorted(scheduled_uops, key=lambda x: x['start_cycle'])

  ports = ['0', '1', '2', '3', '4', '5']
  current_cycle = 0
  while current_cycle < 10:
    for scheduled_uop in scheduled_uops:
      if scheduled_uop['start_cycle'] <= current_cycle and scheduled_uop[
          'start_cycle'] + scheduled_uop['latency'] > current_cycle:
        ports[scheduled_uop['port']] += 'x'
    for index, port in enumerate(ports):
      if len(port) - 2 < current_cycle:
        ports[index] += ' '
    current_cycle += 1

  for port in ports:
    print(port)


if __name__ == '__main__':
  app.run(main)
