import obd
import json
import os
from datetime import datetime

with open("./commands.json", "r") as file:
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
    for cmd in commands_file.keys():
        try:
            response = connection.query(obd.commands[cmd])
            if not response.is_null():
                # Store the value with its unit
                if response.value is not None:
                    sensor_data[cmd.name] = {
                        "value": str(response.value),
                        "unit": str(response.value.units) if hasattr(response.value, 'units') else "N/A"
                    }
        except Exception as e:
            print(f"Error reading {cmd.name}: {e}")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"obd_data_{timestamp}.json"
    filepath = os.path.join(output_folder, filename)

    # Save to JSON file
    with open(filepath, 'w') as f:
        print(sensor_data)
        json.dump(sensor_data, f, indent=4)

    print(f"Data saved to: {filepath}\n")
    print("=" * 50)
    print("SENSOR DATA:")
    print("=" * 50)

    # Print the dictionary
    for sensor, data in sensor_data.items():
        print(f"{sensor}:")
        print(f"  Value: {data['value']}")
        print(f"  Unit: {data['unit']}")
        print(f"  Command: {data['command']}")
        print()

    print("=" * 50)
    print(f"Total sensors read: {len(sensor_data)}")

    return sensor_data


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
