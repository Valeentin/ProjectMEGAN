# Tests connection of two BLE servers at the same time.

import simplepyble
import time
import pprint



# Define the service and characteristic UUIDs
ORANGE_ADDRESS = '6664784B-1446-B3F8-C692-BD64944FBFA6'
RED_ADDRESS = 'A38E949E-036D-6B99-012E-222FDDE5E825'
RED_CHARACTERISTIC_UUID = "1a072b78-68a9-4e3e-9897-2d7bf86f10d8"
ORANGE_CHARACTERISTIC_UUID = "a294e426-3f67-4421-8cb5-a83267de5b7f"


def connect_peripheral(address, char_id):
    adapters = simplepyble.Adapter.get_adapters()

    # Choosing an adapter
    if len(adapters) == 0 or len(adapters) > 1:
            print("NO ADAPTERS FOUND or MORE THAN 1 ADAPTER FOUND")
    elif len(adapters) == 1:
        adapter = adapters[0]

    adapter.scan_for(1000)
    peripherals = adapter.scan_get_results()
    if len([p for p in peripherals if p.address() == address]) == 1:
        peripheral = [p for p in peripherals if p.address() == address][0]
    else:
        print(f"Device with address [{address}] not found.")

    peripheral.connect()

    # Check that the SERVICE_UUID and CHARACTERISTIC_UUID are valid
    services = peripheral.services()
    for service in services:
        for characteristic in service.characteristics():
            if char_id == characteristic.uuid():
                return (service.uuid(), characteristic.uuid()), peripheral

    print(f"Characteristic [{char_id}] not found. ")

    return None, None


red_uuid_pair, red_peripheral = connect_peripheral(RED_ADDRESS, RED_CHARACTERISTIC_UUID)

print("Red Peripheral Connected")


orange_uuid_pair, orange_peripheral = connect_peripheral(ORANGE_ADDRESS, ORANGE_CHARACTERISTIC_UUID)

print("Orange Peripheral Connected")