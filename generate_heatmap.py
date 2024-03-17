"""
Script for generating a heatmap for visualization.
"""

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input file')

flags.mark_flag_as_required('input_file')


def main(_):
  confusion_matrix = []
  for i in range(0, 15):
    inner_array = [0 for j in range(0, 15)]
    confusion_matrix.append(inner_array)
  with open(FLAGS.input_file) as input_file_handle:
    # skip the header
    input_file_handle.readline()
    for input_line in input_file_handle:
      input_line_parts = input_line.split(',')
      uica = int(input_line_parts[1])
      optimal = int(input_line_parts[2])
      if uica > 15 or optimal > 15:
        continue
      confusion_matrix[optimal - 1][uica - 1] += 1

  for inner_array in reversed(confusion_matrix):
    for value in inner_array:
      print(f'{value},', end='')
    print('')


if __name__ == '__main__':
  app.run(main)
