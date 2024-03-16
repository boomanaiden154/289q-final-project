"""
A tool for taking a BHive-esque CSV file and then iterating over all basic
blocks, comparing the uop execution time from uica to the optimal one.
"""

import subprocess
import os
import tempfile
import logging

import ray

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input CSV file.')
flags.DEFINE_string('output_file', None, 'The output CSV file.')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')


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
  return (int(output_lines[-2]), int(output_lines[-3]))


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


@ray.remote(num_cpus=1)
def get_optimal_uica_pair(hex_code):
  with tempfile.TemporaryDirectory() as temp_dir:
    run_uica(hex_code, temp_dir)
    optimal_value, solver_status = get_optimal(hex_code, temp_dir)
    if optimal_value == 0:
      logging.info('skipping optimal value of zero')
      return []
    uica_value = get_uica_value(hex_code, temp_dir)
    did_solver_timeout = solver_status == 9
  return [(uica_value, optimal_value, did_solver_timeout, hex_code)]


def main(_):
  hex_codes = []
  with open(FLAGS.input_file) as input_file_handle:
    # Read the first line here and discard the value to get past the CSV header.
    input_file_handle.readline()
    for input_line in input_file_handle:
      hex_code = input_line.split(',')[0]
      hex_codes.append(hex_code)

  logging.info('Just finished loading data')

  value_futures = []
  for hex_code in hex_codes:
    value_futures.append(get_optimal_uica_pair.remote(hex_code))

  solver_timeouts = 0

  with open(FLAGS.output_file, 'w') as output_file_handle:
    output_file_handle.write(f'hex,uica,optimal\n')
    while len(value_futures) > 0:
      to_return = 64 if len(value_futures) > 128 else 1
      finished, value_futures = ray.wait(
          value_futures, timeout=5.0, num_returns=to_return)
      logging.info(
          f'Just finished {len(finished)}, {len(value_futures)} remaining. Have seen {solver_timeouts} timeouts.'
      )
      for finished_batch in ray.get(finished):
        for finished_value in finished_batch:
          if finished_value[2]:
            solver_timeouts += 1
          output_file_handle.write(
              f'{finished_value[3]},{finished_value[0]},{finished_value[1]}\n')


if __name__ == '__main__':
  app.run(main)
