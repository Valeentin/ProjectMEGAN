#include <ArduinoBLE.h>

#include <TinyMLShield.h>
#include <TensorFlowLite.h>
#include <Arduino_BMI270_BMM150.h>
#include <tensorflow/lite/micro/all_ops_resolver.h>
#include <tensorflow/lite/micro/micro_error_reporter.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/schema/schema_generated.h>
#include <tensorflow/lite/version.h>
#include "Lmodel.h"

// -------------------------- TENSOR FLOW MODEL AND GESTURE SETUP -------------------------- 
const float accelerationThreshold = 2.5; // threshold of significant in G's
const int numSamples = 119;

int samplesRead = numSamples;

// global variables used for TensorFlow Lite (Micro)
tflite::MicroErrorReporter tflErrorReporter;

// pull in all the TFLM ops, you can remove this line and
// only pull in the TFLM ops you need, if would like to reduce
// the compiled size of the sketch.
tflite::AllOpsResolver tflOpsResolver;

const tflite::Model* tflModel = nullptr;
tflite::MicroInterpreter* tflInterpreter = nullptr;
TfLiteTensor* tflInputTensor = nullptr;
TfLiteTensor* tflOutputTensor = nullptr;

// Create a static memory buffer for TFLM, the size may need to
// be adjusted based on the model you are using
constexpr int tensorArenaSize = 8 * 1024;
byte tensorArena[tensorArenaSize] __attribute__((aligned(16)));

// array to map gesture index to a name
const char* GESTURES[] = {
  "TWIST",
  "RAISE",
  "CROSS",
  "FLEX",
};
#define NUM_GESTURES (sizeof(GESTURES) / sizeof(GESTURES[0]))


//  -----------------------------------  BLE SETUP --------------------------------------- 
BLEService* motionService = nullptr;

BLEByteCharacteristic* experimentStart = nullptr;
BLEByteCharacteristic* moveCompleteCharacteristic0 = nullptr;
BLEByteCharacteristic* moveCompleteCharacteristic1 = nullptr;
BLEByteCharacteristic* gestureCompleteCharacteristic0 = nullptr;
BLEByteCharacteristic* gestureCompleteCharacteristic1 = nullptr;
BLEByteCharacteristic* gestureCharacteristic = nullptr;


void resetChars() {
  // Write '0' to all characteristics. Uses UTF-8 encoding.
  experimentStart->writeValue((byte)0x00);
  moveCompleteCharacteristic0->writeValue((byte)0x00); // Time to complete Gesture
  moveCompleteCharacteristic1->writeValue((byte)0x00);
  gestureCompleteCharacteristic0->writeValue((byte)0x00); // Time to complete computations
  gestureCompleteCharacteristic1->writeValue((byte)0x00);
  gestureCharacteristic->writeValue((byte)0x00); // Which gesture was completed
}

void setup() {
  // Setup serial connection.
  Serial.begin(9600);
  // while (!Serial);

  // -------------------------- BLE SETUP --------------------------
  motionService = new BLEService("7e140f58-cd90-4aa9-b4a5-29b74a7bb3fd"); // BLE LED Service

  experimentStart = new BLEByteCharacteristic("911172d0-ab12-48f0-8d71-648c6c33bfec", BLERead | BLEWrite);
  moveCompleteCharacteristic0 = new BLEByteCharacteristic("09fc7423-502a-4e2e-ba72-7122381f1c4d", BLERead | BLEWrite);
  moveCompleteCharacteristic1 = new BLEByteCharacteristic("579d1be1-c066-435c-8f11-76d75e03f319", BLERead | BLEWrite);
  gestureCompleteCharacteristic0 = new BLEByteCharacteristic("deaeaf0a-d25e-4427-a681-5968e7459752", BLERead | BLEWrite);
  gestureCompleteCharacteristic1 = new BLEByteCharacteristic("c3b6591f-3d60-407c-b295-c423ce5e7bc8", BLERead | BLEWrite);
  gestureCharacteristic = new BLEByteCharacteristic("a294e426-3f67-4421-8cb5-a83267de5b7f", BLERead | BLEWrite);
  
  // Set LED's pin to output mode
  pinMode(LEDR, OUTPUT);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDB, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  digitalWrite(LED_BUILTIN, LOW);         // when the central disconnects, turn off the LED
  digitalWrite(LEDR, HIGH);               // will turn the LED off
  digitalWrite(LEDG, HIGH);               // will turn the LED off
  digitalWrite(LEDB, HIGH);                // will turn the LED off
  
  // Begin initialization
  if (!BLE.begin()) {
    Serial.println("starting Bluetooth® Low Energy failed!");

    // If failure, do not proceed
    while (1);
  }
  
  // Set advertised local name and service UUID:
  BLE.setLocalName("Nano 33 BLE Sense Red");
  BLE.setAdvertisedService(*motionService);

  // Add the characteristics to the service
  motionService->addCharacteristic(*experimentStart);
  motionService->addCharacteristic(*moveCompleteCharacteristic0);
  motionService->addCharacteristic(*moveCompleteCharacteristic1);
  motionService->addCharacteristic(*gestureCompleteCharacteristic0);
  motionService->addCharacteristic(*gestureCompleteCharacteristic1);
  motionService->addCharacteristic(*gestureCharacteristic);
  
  // add service
  BLE.addService(*motionService);
  
  resetChars();

  // Start advertising
  BLE.advertise();

  Serial.println("BLE LED Peripheral Red");

  // -------------------------- IMU SETUP --------------------------

  // initialize the IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  // print out the samples rates of the IMUs
  Serial.print("Accelerometer sample rate = ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println(" Hz");
  Serial.print("Gyroscope sample rate = ");
  Serial.print(IMU.gyroscopeSampleRate());
  Serial.println(" Hz");

  Serial.println();

  // get the TFL representation of the model byte array
  tflModel = tflite::GetModel(Lmodel);
  if (tflModel->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Model schema mismatch!");
    while (1);
  }

  // Create an interpreter to run the model
  tflInterpreter = new tflite::MicroInterpreter(tflModel, tflOpsResolver, tensorArena, tensorArenaSize, &tflErrorReporter);

  // Allocate memory for the model's input and output tensors
  tflInterpreter->AllocateTensors();

  // Get pointers for the model's input and output tensors
  tflInputTensor = tflInterpreter->input(0);
  tflOutputTensor = tflInterpreter->output(0);
}

void loop() {
  // 
  float aX, aY, aZ, gX, gY, gZ;

  
  // Listen for BLE peripherals
  BLEDevice central = BLE.central();

  // If a central is connected to peripheral:
  if (central) {
  //if (true) {
    
    Serial.print("Connected to central: ");
    // Print the central's MAC address:
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, HIGH); // Turn on the LED to indicate the connection

    delay(1000);
    
    while (central.connected()) {
    //while (true) {

      
      if ((experimentStart->value() == 0)) {
        delay(1);
        continue;
        }
      
      Serial.println("EXPERIMENT STARTED.");
      unsigned long startTime = millis();

      // wait for significant motion
      while (samplesRead == numSamples) {
        
        if (IMU.accelerationAvailable()) {
          // read the acceleration data
          IMU.readAcceleration(aX, aY, aZ);

          // sum up the absolutes
          float aSum = fabs(aX) + fabs(aY) + fabs(aZ);


          // check if it's above the threshold
          if (aSum >= accelerationThreshold) {
            // reset the sample read count
            samplesRead = 0;
            break;
          }

          // Serial.println("IMU read, below threshold.");
        }
      }

      unsigned long curTime = millis();
      uint16_t moveTime = curTime - startTime;
      Serial.println("Reaction time: " + String(moveTime) + " milliseconds.");

      bool isDoneMoving = false;
      float accSum;
      uint16_t gestureTime;
      // Read all the samples. Do not stop until numSamples is read.
      while (samplesRead < numSamples) {
        // check if new acceleration AND gyroscope data is available
        if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
          // read the acceleration and gyroscope data
          IMU.readAcceleration(aX, aY, aZ);
          IMU.readGyroscope(gX, gY, gZ);

          accSum = fabs(aX) + fabs(aY) + fabs(aZ);

          // If we are above acc thresh AND move complete. Mark move not complete.
          if ((accSum >= accelerationThreshold) & (isDoneMoving)) {
            isDoneMoving = false;
            }
          // If we are below acc thresh AND move not complete. Mark as complete.
          else if ((accSum <= accelerationThreshold) & (!isDoneMoving)) {
              isDoneMoving = true;
              curTime = millis();
              gestureTime = curTime - startTime;
            }

          // normalize the IMU data between 0 to 1 and store in the model's
          // input tensor
          tflInputTensor->data.f[samplesRead * 6 + 0] = (aX + 4.0) / 8.0;
          tflInputTensor->data.f[samplesRead * 6 + 1] = (aY + 4.0) / 8.0;
          tflInputTensor->data.f[samplesRead * 6 + 2] = (aZ + 4.0) / 8.0;
          tflInputTensor->data.f[samplesRead * 6 + 3] = (gX + 2000.0) / 4000.0;
          tflInputTensor->data.f[samplesRead * 6 + 4] = (gY + 2000.0) / 4000.0;
          tflInputTensor->data.f[samplesRead * 6 + 5] = (gZ + 2000.0) / 4000.0;

          samplesRead++;

        }
      }

      // If we never finished the move, update the time.
      if (!isDoneMoving) {
        curTime = millis();
        gestureTime = curTime - startTime;
      }
    
      Serial.println("Movement time: " + String(gestureTime) + " milliseconds.");


      // Run inferencing
      TfLiteStatus invokeStatus = tflInterpreter->Invoke();
      
      if (invokeStatus != kTfLiteOk) {
        Serial.println("Invoke failed!");
        while (1);
        return;
      }

      // Find the gesture with the highest confidence
      int gestureIndex = -1;
      float maxConfidence = -1.0;

      for (int i = 0; i < NUM_GESTURES; i++) {
        if (tflOutputTensor->data.f[i] > maxConfidence) {
          maxConfidence = tflOutputTensor->data.f[i];
          gestureIndex = i;
        }
      }

      // Print the recognized gesture
      Serial.print("Recognized Gesture: ");
      if (gestureIndex >= 0) {
        Serial.println(GESTURES[gestureIndex]);
        Serial.println(gestureIndex);
      } else {
        Serial.println("Unknown");
      }

      Serial.println();

      
      moveCompleteCharacteristic0->writeValue((uint8_t)(moveTime));
      moveCompleteCharacteristic1->writeValue((uint8_t)(moveTime >> 8));

      gestureCompleteCharacteristic0->writeValue((uint8_t)(gestureTime));
      gestureCompleteCharacteristic1->writeValue((uint8_t)(gestureTime >> 8));

      
      gestureCharacteristic->writeValue((uint8_t) gestureIndex);


      while (central.connected() and !(experimentStart->value() == 0)) {
      // Wait for python script to read values. 
      // Python script writes to experimentStart when done.
      delay(50);
      }
      
      resetChars();
      
    }
    

    // when the central disconnects, print it out:
    Serial.print(F("Disconnected from central: "));
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, LOW);         // when the central disconnects, turn off the LED
    digitalWrite(LEDR, HIGH);          // will turn the LED off
    digitalWrite(LEDG, HIGH);        // will turn the LED off
    digitalWrite(LEDB, HIGH);         // will turn the LED off
    
  }
}
