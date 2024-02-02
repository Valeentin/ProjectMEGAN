import asyncio
from bleak import BleakClient

# Define the service and characteristic UUIDs
SERVICE_UUID = "1a072b78-68a9-4e3e-9897-2d7bf86f10d8"
CHARACTERISTIC_UUID = "a294e426-3f67-4421-8cb5-a83267de5b7f"

async def write_to_characteristic(address):
    while True:
        try:
            # Prompt the user for a new value
            user_input = input("Enter a new value (integer), or 'q' to quit: ")
            
            if user_input.lower() == 'q':
                break  # Exit the loop if the user enters 'q'
            
            new_value = int(user_input, base=0)

            async with BleakClient(address) as client:

                # Write the new value
                await client.write_gatt_char(CHARACTERISTIC_UUID, bytearray([new_value]))

        except asyncio.CancelledError:
            # Catch the CancelledError to handle disconnection
            print("Device disconnected. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Replace 'your_device_address' with the actual address of your BLE peripheral device
    device_address = "6664784B-1446-B3F8-C692-BD64944FBFA6" # ORANGE DEVICE

    # Run the event loop
    asyncio.run(write_to_characteristic(device_address))