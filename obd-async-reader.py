import obd
import json
import os
import time

with open("./commands.json", "r") as file:
    commands_file = json.load(file)

connection = obd.Async(delay_cmds=0.05)

# Your 16 commands
commands = [obd.commands[key] for key in commands_file.keys()]

# Watch all commands
for cmd in commands:
    connection.watch(cmd)

connection.start()

# Wait for first full cycle
time.sleep(2)

# Now you can read all 16 values instantly in a loop
while True:
    start = time.process_time()
    for cmd in commands:
        response = connection.query(cmd)
        if not response.is_null():
            print(f"{cmd.name}: {response.value}")
    print("Total time for this run : ", time.process_time() - start)
