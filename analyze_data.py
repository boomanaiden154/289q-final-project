"""
Script for analyzing data and generating confusion matrices and what not.
"""

import logging
import statistics

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input CSV file.')

flags.mark_flag_as_required('input_file')


def main(_):
  with open(FLAGS.input_file) as input_file_handle:
    # Read the first line to get past the header
    input_file_handle.readline()
    percents = []
    for line in input_file_handle:
      line_parts = line.split(',')
      uica_value = float(line_parts[1])
      optimal_value = float(line_parts[2])
      percent = 1 - (optimal_value / uica_value)
      percents.append(percent)

    logging.info(statistics.mean(percents))


if __name__ == '__main__':
  app.run(main)
