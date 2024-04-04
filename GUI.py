import cv2
import numpy as np
from gtts import gTTS
import os

class GUI:
    def __init__(self):
        self.screen = np.zeros((480, 640, 3), dtype=np.uint8)  # Initialize black screen

    def display_text(self, text):
        self.screen = np.zeros((480, 640, 3), dtype=np.uint8) # Reset to black
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.75
        font_thickness = 1

        # Split text into lines
        lines = text.split('\n')

        # Initialize y-coordinate for the first line
        y = 100

        # Draw each line of text
        for line in lines:
            print(line)
            # Calculate text size and positio
            text_size = cv2.getTextSize(line, font, font_scale, font_thickness)[0]
            text_x = (self.screen.shape[1] - text_size[0]) // 2
            text_y = y

            # Draw text on screen
            cv2.putText(self.screen, line, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)

            # Update y-coordinate for the next line
            y += text_size[1] + 10  # Add some spacing between lines


        # Show updated screen
        cv2.imshow('Screen', self.screen)
        cv2.waitKey(30)

    def display_color(self, color=(0, 0, 0)):
        self.screen[:] = color
        cv2.imshow('Screen', self.screen)
        cv2.waitKey(30)

    def read_text(self, text):
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        os.system("mpg123 temp.mp3")

    def read_audio(self, path):
        os.system(f"mpg123  {path}")

    def display_and_read_text(self, text):
        self.display_text(text)
        self.read_text(text.replace("\n", ""))

    def audio_instructions(self):
        # self.display_and_read_text("Welcome to the MEGAN Protocol's series of \n"
        #                            "auditory coordination tests. Each of the \n"
        #                             "four gestures demonstrated for you will be \n"
        #                             "mapped to a color. For each trial, wait for \n"
        #                             "the computer to announce a color. Then, \n"
        #                             "perform the gesture in one smooth motion. \n"
        #                             "After completing the move, stand still and \n"
        #                             "wait for the computer's instructions. \n"
        #                             "The color mapping is shown on the \n"
        #                             " next slide. \n")
        return
    def visual_instructions(self):
        # self.display_and_read_text("Welcome to the MEGAN Protocol's series of \n"
        #                            "visual coordination tests. Each of the \n"
        #                             "four gestures demonstrated for you will be \n"
        #                             "mapped to a color. For each trial, wait for \n"
        #                             "the computer to display a color. Then, \n"
        #                             "perform the gesture in one smooth motion. \n"
        #                             "After completing the move, stand still and \n"
        #                             "wait for the computer's instructions. \n"
        #                             "The color mapping is shown on the \n"
        #                             " next slide. \n")
        return
    def setup_complete(self):
        self.display_and_read_text("Setup and connection complete. \n Press enter once to begin.")
        cv2.waitKey(0)

    def display_color_mapping(self, color_mapping):
        sector_height = self.screen.shape[0] // 2
        sector_width = self.screen.shape[1] // 2

        # Define colors and corresponding labels
        colors = {"GREEN": (0, 128, 0),
                  "BLUE": (128, 0, 0),
                  "RED": (0, 0, 128),
                  "ORANGE": (0, 128, 200)}

        labels = ["TWIST", "RAISE", "CROSS", "FLEX"]

        # Iterate over color_mapping and color the corresponding sector
        for i, color in enumerate(color_mapping):
            y_start = (i // 2) * sector_height
            y_end = y_start + sector_height
            x_start = (i % 2) * sector_width
            x_end = x_start + sector_width

            # Color the sector
            self.screen[y_start:y_end, x_start:x_end] = colors[color]

            # Write label in the center of the sector
            label = labels[i]
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_x = x_start + (sector_width - text_size[0]) // 2
            text_y = y_start + (sector_height + text_size[1]) // 2

            cv2.putText(self.screen, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Show updated screen
        cv2.imshow('Screen', self.screen)
        cv2.waitKey(50)
        self.read_text("Once you have memorized the mapping, press any key to continue.")
        cv2.waitKey(0)

