import simplepyble
import time
import pandas as pd
import random
from BLEPeripheral import BLEPeripheral
import struct
import time
import numpy as np
from GUI import GUI


TEST_FORMAT = ["AUDIO", "VISUAL"]  # [Audio, Visual]
IS_RANDOMIZED = False
RANDOM_PAUSE_DURATION = 1 # Seconds


GESTURES = ["TWIST", "RAISE", "CROSS", "FLEX"]

orange_address = "6664784B-1446-B3F8-C692-BD64944FBFA6"
orange_service = "7e140f58-cd90-4aa9-b4a5-29b74a7bb3fd"
orange_experiment_start = "911172d0-ab12-48f0-8d71-648c6c33bfec"
orange_move_complete0 = "09fc7423-502a-4e2e-ba72-7122381f1c4d"
orange_move_complete1 = "579d1be1-c066-435c-8f11-76d75e03f319"
orange_gesture_complete0 = "deaeaf0a-d25e-4427-a681-5968e7459752"
orange_gesture_complete1 = "c3b6591f-3d60-407c-b295-c423ce5e7bc8"
orange_gesture = "a294e426-3f67-4421-8cb5-a83267de5b7f"

COLORS = {"GREEN": (0, 128, 0),
        "BLUE": (128, 0, 0),
        "RED": (0, 0, 128),
        "ORANGE": (0, 128, 200),
        "BLACK": (0, 0, 0)}



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

def write_peripheral(address, char_id, value):
    s_c_pair, peripheral = connect_peripheral(address, char_id)

    # Write the content to the characteristic
    # Note: `write_request` required the payload to be presented as a bytes object.
    peripheral.write_request(s_c_pair[0], s_c_pair[1], str.encode(value))
    peripheral.disconnect()

# Read peripheral.
def read_peripheral(address, char_id):
    s_c_pair, peripheral = connect_peripheral(address, char_id)
    bytes_value = peripheral.read(s_c_pair[0], s_c_pair[1])
    value = bytes_value.decode()
    peripheral.disconnect()

def read_until_found(address, char_id, values):
    s_c_pair, peripheral = connect_peripheral(address, char_id)
    start_time = time.time()
    while (time.time() - start_time) < SEARCH_TIMEOUT:
        bytes_value = peripheral.read(s_c_pair[0], s_c_pair[1])
        value = bytes_value.decode()
        if value in values:
            return value
        time.sleep(.1)
        continue
    return "-1"


def reset_test(address, char_id):
    # Send 0 to signify test reset
    write_peripheral(address, char_id, "0")


def gesture_test(gesture):
    reset_test(RED_ADDRESS, CHARACTERISTIC_UUID)

    print(f"\n --------- Perform the [{gesture}] gesture. --------- \n")

    # Start timer
    start_time = time.time()

    # Wait for BLE variable to be updated
    while True:
        value = read_until_found(RED_ADDRESS, CHARACTERISTIC_UUID, GESTURES)
        if value == "1":
            print(f"[{gesture}] gesture completed successfully!")
            break
        elif value == "2":
            print(f"[{gesture}] gesture not completed properly. Wait for instructions and try again.")
            break
        elif value == "-1":
            print(f"ERROR. Arduino has not updated the gesture variable.")
        elif time.time() - start_time > MAX_GESTURE_TIME:  # Adjust the timeout as needed
            print(f"FAILED. [{gesture}] gesture was not completed in the minimum time {MAX_GESTURE_TIME}.")
            break

        time.sleep(2)

def create_trials():
    color_mapping = ["GREEN", "BLUE", "RED", "ORANGE"]
    trial_set  = [0] * 3 + [1] * 3 + [2] * 2 + [3] * 2 # 10 trials. 3 TWIST, 3 RAISE, 2 CROSS, 2 FLEX

    random.shuffle(color_mapping) # Shuffle color mapping
    random.shuffle(trial_set) # Shuffled trial set


    return color_mapping, trial_set

# Connect via BT
print("Connecting to Arduino...")
orange = BLEPeripheral(orange_address)
orange.connect()
print("Connection Success!")

main_gui = GUI()

main_gui.setup_complete()

# For each test in the lineup
for test_type in TEST_FORMAT:
    # Read Audio or Visual Test Instructions
    if test_type == "AUDIO":
        main_gui.audio_instructions()
        is_visual_test = False
    elif test_type == "VISUAL":
        main_gui.visual_instructions()
        is_visual_test = True
    else:
        raise ValueError(f"Error. Test requested was '{test_type}'. Tests should be either 'AUDIO' or 'VISUAL.'")

    
     # Generate Color Mapping
    if IS_RANDOMIZED:
        color_mapping, trial_set = create_trials()
    else:
        color_mapping = ["GREEN", "BLUE", "RED", "ORANGE"]
        trial_set = [1] # TWIST, RAISE, CROSS, FLEX
     

    time.sleep(1.5)

    main_gui.display_color_mapping(color_mapping)
    main_gui.display_and_read_text("Beginning testing. Assume your resting position.")

    time.sleep(1.5)

    trial_results = []

    # For each test
    for i in trial_set:
        # 3 total attempts.
        color_string = color_mapping[i]
        gesture = GESTURES[i]
        success = False

        for attempt in range(1, 4):
            if (is_visual_test):
                # TODO: Visual Test Code
                main_gui.display_and_read_text("Get ready. The visual test will begin in 3. 2. 1.")
                time.sleep(random.random() * RANDOM_PAUSE_DURATION)
                main_gui.display_color(COLORS[color_string])
            else:
                # TODO: Audio Test Code
                main_gui.display_and_read_text("Get ready. The audio test will begin in 3. 2. 1.")
                time.sleep(random.random() * RANDOM_PAUSE_DURATION)
                main_gui.display_color(COLORS["BLACK"])
                main_gui.read_audio(f"./audio_samples/{color_string}.mp3")

            orange.write(orange_service, orange_experiment_start, struct.pack('<B', 1))
            
            # Perform test with BLE.

            val0 = b'\x00'

            while val0 == b'\x00' or val0 == None:
                val0 = orange.read(orange_service, orange_move_complete0)
            
            val1 = orange.read(orange_service, orange_move_complete1)
            val2 = orange.read(orange_service, orange_gesture_complete0)
            val3 = orange.read(orange_service, orange_gesture_complete1)
            val4 = orange.read(orange_service, orange_gesture)

            reaction_time = struct.unpack('<H', val0 + val1)[0]
            move_time = struct.unpack('<H', val2 + val3)[0]
            gesture_index = struct.unpack('<B', val4)[0]
            

            #print(f"Reaction Time: {reaction_time} milliseconds.")
            #print(f"Move Time: {move_time} milliseconds.")
            #print(f"Gesture Detected: {gesture_index}")

            # Reset all values and give arduino reset signal.
            val0 = b'\x00'
            val1 = b'\x00'
            val2 = b'\x00'
            val3 = b'\x00'
            val4 = b'\x00'
            orange.write(orange_service, orange_experiment_start, struct.pack('<B', 0))
            
            gesture_detected = GESTURES[gesture_index]
            if gesture_index == i:
                success = True
            else:
                success = False
            
            # print(f"TRIAL RESULT: \n [attmpt, colr, gest, succ, react, move]] \n  {[attempt, color, gesture, gesture_detected, success, reaction_time, move_time]} \n")
            trial_results.append([attempt, color_string, gesture, gesture_detected, success, reaction_time, move_time])

            # TODO: Tracking complete
            main_gui.display_and_read_text("TRACKING COMPLETE. \n Please return to resting position.")

            time.sleep(3)


            if success:
                break  # Exit the loop if the user succeeds


    df = pd.DataFrame(trial_results, columns=["Attempt", "Color", "Gesture Detected", "Gesture Requested", "Success", "Reaction Time", "Move Time"])

    df.to_csv(f'{test_type}.csv')



# print("Connecting to Arduino...")

# UUIDS_PAIR, peripheral = connect_peripheral(RED_ADDRESS, CHARACTERISTIC_UUID)

# if peripheral is not None:
#     print("Connection success.")
#     peripheral.disconnect()
#     try:
#         for gesture in GESTURES:
#             input(f"\nPress Enter to start {gesture} gesture test...")
#             gesture_test(gesture)
#     finally:
#         print("Test Complete")


# write_peripheral(RED_ADDRESS, CHARACTERISTIC_UUID, "2")
# read_peripheral(RED_ADDRESS, CHARACTERISTIC_UUID)