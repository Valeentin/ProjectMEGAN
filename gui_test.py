from GUI import GUI
import time


# Example usage:
gui = GUI()

time.sleep(1)

# Display text
gui.audio_instructions()
time.sleep(3)
gui.display_color_mapping(["RED", "GREEN", "ORANGE", "BLUE"])