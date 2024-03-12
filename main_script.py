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
IS_RANDOMIZED = False # Runs raise once. If randomized, STD trial.
RANDOM_PAUSE_DURATION = 1 # Seconds
IS_RIGHT_HAND = True # Right hand = Orange, Left hand = Red


GESTURES = ["TWIST", "RAISE", "CROSS", "FLEX"]

if IS_RIGHT_HAND:
    ble_address = "6664784B-1446-B3F8-C692-BD64944FBFA6"
else:
    ble_address = "A38E949E-036D-6B99-012E-222FDDE5E825"
ble_service = "7e140f58-cd90-4aa9-b4a5-29b74a7bb3fd"
ble_experiment_start = "911172d0-ab12-48f0-8d71-648c6c33bfec"
ble_move_complete0 = "09fc7423-502a-4e2e-ba72-7122381f1c4d"
ble_move_complete1 = "579d1be1-c066-435c-8f11-76d75e03f319"
ble_gesture_complete0 = "deaeaf0a-d25e-4427-a681-5968e7459752"
ble_gesture_complete1 = "c3b6591f-3d60-407c-b295-c423ce5e7bc8"
ble_gesture = "a294e426-3f67-4421-8cb5-a83267de5b7f"

COLORS = {"GREEN": (0, 128, 0),
        "BLUE": (128, 0, 0),
        "RED": (0, 0, 128),
        "ORANGE": (0, 128, 200),
        "BLACK": (0, 0, 0)}


def create_trials():
    color_mapping = ["GREEN", "BLUE", "RED", "ORANGE"]
    trial_set  = [0] * 3 + [1] * 3 + [2] * 2 + [3] * 2 # 10 trials. 3 TWIST, 3 RAISE, 2 CROSS, 2 FLEX

    random.shuffle(color_mapping) # Shuffle color mapping
    random.shuffle(trial_set) # Shuffled trial set


    return color_mapping, trial_set

# Connect via BT
print("Connecting to Arduino...")
orange = BLEPeripheral(ble_address)
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

            orange.write(ble_service, ble_experiment_start, struct.pack('<B', 1))
            
            # Perform test with BLE.

            val4 = b'\x00'

            while val4 == b'\x00' or val4 == None:
                val4 = orange.read(ble_service, ble_gesture)
            
            val0 = orange.read(ble_service, ble_move_complete0)
            val1 = orange.read(ble_service, ble_move_complete1)
            val2 = orange.read(ble_service, ble_gesture_complete0)
            val3 = orange.read(ble_service, ble_gesture_complete1)

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
            orange.write(ble_service, ble_experiment_start, struct.pack('<B', 0))
            
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

    if IS_RIGHT_HAND:
        df.to_csv(f'{test_type}_RIGHT.csv')
    else:
        df.to_csv(f'{test_type}_LEFT.csv')