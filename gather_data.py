"""
A tool for taking a BHive-esque CSV file and then iterating over all basic
blocks, comparing the uop execution time from uica to the optimal one.
"""

import subprocess
import os
import tempfile

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input CSV file.')

flags.mark_flag_as_required('input_file')


def run_uica(hex_code, temp_dir):
  json_output_path = os.path.join(temp_dir, 'uica_output.json')
  uica_command_vector = [
      '/uica/uiCA.py', '-hex', hex_code, '-arch=SNB',
      f'-json={json_output_path}'
  ]
  uica_output = subprocess.run(
      uica_command_vector, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if uica_output.returncode != 0:
    print(hex_code)
  assert (uica_output.returncode == 0)


def get_optimal(hex_code, temp_dir):
  json_input_path = os.path.join(temp_dir, 'uica_output.json')
  json_output_path = os.path.join(temp_dir, 'uop_schedule.json')
  optimal_command_vector = [
      'python3', '/eec289q-final-project/solve_ilp_instance.py',
      f'--input_file={json_input_path}', f'--output_file={json_output_path}'
  ]
  optimal_output = subprocess.run(
      optimal_command_vector, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if (optimal_output.returncode != 0):
    print(optimal_output.stdout)
    print(hex_code)
  assert (optimal_output.returncode == 0)
  output = optimal_output.stdout.decode('utf-8')
  output_lines = output.split('\n')
  return int(output_lines[-2])


def get_uica_value(hex_code, temp_dir):
  json_input_path = os.path.join(temp_dir, 'uica_output.json.uica')
  uica_value_command_vector = [
      'python3', '/eec289q-final-project/parse_uica_json.py',
      f'--input_file={json_input_path}'
  ]
  uica_value_output = subprocess.run(
      uica_value_command_vector,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT)
  if uica_value_output.returncode != 0:
    print(hex_code)
  assert (uica_value_output.returncode == 0)
  output_lines = uica_value_output.stdout.decode('utf-8').split('\n')
  return int(output_lines[-2])


def main(_):
  value_pairs = []
  with open(FLAGS.input_file) as input_file_handle:
    # Read the first line here and discard the value to get past the CSV header.
    input_file_handle.readline()
    for input_line in input_file_handle:
      hex_code = input_line.split(',')[0]
      with tempfile.TemporaryDirectory() as temp_dir:
        run_uica(hex_code, temp_dir)
        optimal_value = get_optimal(hex_code, temp_dir)
        uica_value = get_uica_value(hex_code, temp_dir)
        value_pairs.append((uica_value, optimal_value))
      print('just finished a BB')


if __name__ == '__main__':
  app.run(main)
