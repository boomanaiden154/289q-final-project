"""
Tooling for generating and solving ILP instances for individual basic blocks
to determine optimal scheduling.
"""

import json
import gurobipy

from absl import flags
from absl import app

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input JSON file containing uops')
flags.DEFINE_string('output_file', None,
                    'The output JSON file containing the schedule')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')


def main(_):
  with open(FLAGS.input_file) as input_file_handle:
    uops = json.load(input_file_handle)

  model = gurobipy.Model()

  # Setup a variable for the maximum cycle. Then we can add a constraint
  # per variable that the variable must be less than the maximum, and then
  # we minimize the maximum.
  max_cycle = model.addVar(vtype='I', name='max_cycle')

  for index, uop in enumerate(uops):
    # Setup the dependency constraints
    uop_start = model.addVar(vtype='I', name=f'uop{index}-start')
    for dependency in uop['dependencies']:
      latency = uops[dependency]['latency']
      model.addConstr(uop_start - uops[dependency]['start_cycle'] >= latency)
    uop['start_cycle'] = uop_start

    # Set up the maximum constraint
    model.addConstr(uop_start + uop['latency'] <= max_cycle)

    # Set up the port constraints
    possible_ports = [
        int(possible_port) for possible_port in uop['possible_ports']
    ]
    port_variable_sum = gurobipy.LinExpr()

    port_variables = {}
    # Sandy bridge has six execution ports.
    for i in possible_ports:
      is_port_i_used = model.addVar(vtype='B', name=f'uop{index}-port{i}')
      port_variable_sum.add(is_port_i_used)
      port_variables[i] = is_port_i_used

    uop['port_variables'] = port_variables

    model.addConstr(port_variable_sum == 1)

  # Add port conflict constraints
  for index1, uop1 in enumerate(uops):
    possible_ports1 = [
        int(possible_port) for possible_port in uop1['possible_ports']
    ]
    for index2, uop2 in enumerate(uops[index1:], start=index1):
      if index1 == index2:
        continue
      possible_ports2 = [
          int(possible_port) for possible_port in uop2['possible_ports']
      ]
      for possible_port in possible_ports1:
        if possible_port in possible_ports2:
          print(f'{index1}:{possible_port} and {index2}:{possible_port}')
          uop1_port_var = uop1['port_variables'][possible_port]
          uop2_port_var = uop2['port_variables'][possible_port]
          test = model.addVar(vtype='B')
          model.addConstr(test == gurobipy.and_(uop1_port_var, uop2_port_var))
          test2 = model.addVar(vtype='B')
          max_value = 100000
          model.addGenConstrIndicator(
              test, True, uop1['start_cycle'] + uop1['latency']
              <= uop2['start_cycle'] + max_value - test2 * max_value)
          model.addGenConstrIndicator(
              test, True, uop2['start_cycle'] + uop2['latency']
              <= uop1['start_cycle'] + test2 * max_value)

  model.setObjective(max_cycle, gurobipy.GRB.MINIMIZE)

  model.optimize()

  print(f'Solution takes {int(model.getObjective().getValue())} cycles')

  for uop in uops:
    assigned_port = -1
    for port_var in uop['port_variables']:
      if int(uop['port_variables'][port_var].X) == 1:
        assigned_port = port_var
        break
    uop['assigned_port'] = assigned_port

  for index, uop in enumerate(uops):
    print(
        f'{index} Starting at cycle {uop["start_cycle"].X} on port {uop["assigned_port"]}'
    )

  scheduled_uops = []
  for uop in uops:
    scheduled_uop = {
        'port': uop['assigned_port'],
        'latency': uop['latency'],
        'start_cycle': int(uop['start_cycle'].X)
    }
    scheduled_uops.append(scheduled_uop)

  with open(FLAGS.output_file, 'w') as output_file_handle:
    json.dump(scheduled_uops, output_file_handle, indent=2)

  print(int(model.getObjective().getValue()))


if __name__ == '__main__':
  app.run(main)
