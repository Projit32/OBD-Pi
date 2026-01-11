import obd
import json
import time

with open("./commands.json", "r") as file:
    commands_file = json.load(file)

connection = obd.Async(delay_cmds=0.05)

# Your 16 commands
commands = [obd.commands[key] for key in commands_file]

# Watch all commands
for cmd in commands:
    connection.watch(cmd)

connection.start()

# Wait for first full cycle
time.sleep(2)
list_of_data = []
# Now you can read all 16 values instantly in a loop
for i in range(200):
    readings = {}
    start = time.time()
    for cmd in commands:
        response = connection.query(cmd)
        if not response.is_null():
            # print(f"{cmd.name}: {response.value}")
            readings[cmd.name] = {
                "value": str(response.value),
                "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
            }
    list_of_data.append(readings)
    print("Total time for this run : ", time.time() - start)
    time.sleep(0.5)

print(len(list_of_data))
with open("log.dump.json", "w") as f:
    json.dump(list_of_data, f)

print("file written Successfully")
