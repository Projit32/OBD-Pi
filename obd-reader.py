import obd
import json
import os
import time

with open("running.json", "r") as file:
    commands_file = json.load(file)



def fetch_obd_data(connection):
    """
    Fetches all available sensor data from an existing OBD2 connection,
    saves to JSON file, and prints the results.
    """

    # Create output folder if it doesn't exist
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    print("\nFetching sensor data...\n")

    # Dictionary to store sensor data
    sensor_data = {}

    # Get all supported commands
    #supported_commands = connection.supported_commands

    # Query each supported command
    start = time.time()
    for cmd in commands_file:
        try:
            response = connection.query(obd.commands[cmd])
            if not response.is_null():
                # Store the value with its unit
                if response.value is not None:
                    sensor_data[cmd] = {
                        "value": str(response.value),
                        "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                    }
                    print(sensor_data[cmd])
        except Exception as e:
            print(f"Error reading {cmd.name}: {e}")

    print("Total time for this run : ", round(time.time() - start, 2))



if __name__ == "__main__":
    print("Starting continuous OBD2 data collection...")
    print("Connecting to OBD2 interface...")

    connection = None

    try:
        # Connect once
        connection = obd.OBD()  # Auto-connects to USB or RF port

        if not connection.is_connected():
            print("Failed to connect to OBD2 interface!")
            exit(1)

        print(f"Connected to: {connection.port_name()}")
        print("Press Ctrl+C to stop\n")

        # Continuous loop
        while True:
            data = fetch_obd_data(connection)
            print("\nWaiting for next reading...\n")

    except KeyboardInterrupt:
        print("\n\nStopping data collection...")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Close connection when exiting
        if connection and connection.is_connected():
            connection.close()
            print("Connection closed.")
        print("Goodbye!")
