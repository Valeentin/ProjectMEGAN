#include <ArduinoBLE.h>

BLEService ledService("80695f0e-0653-4fe9-be91-a59e985b22c2"); // BLE LED Service

// BLE LED Switch Characteristic - custom 128-bit UUID, read and writable by central
BLEByteCharacteristic switchCharacteristic("1a072b78-68a9-4e3e-9897-2d7bf86f10d8", BLERead | BLEWrite);

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // set LED's pin to output mode
  pinMode(LEDR, OUTPUT);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDB, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  digitalWrite(LED_BUILTIN, LOW);         // when the central disconnects, turn off the LED
  digitalWrite(LEDR, HIGH);               // will turn the LED off
  digitalWrite(LEDG, HIGH);               // will turn the LED off
  digitalWrite(LEDB, HIGH);                // will turn the LED off

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting Bluetooth® Low Energy failed!");

    while (1);
  }

  // set advertised local name and service UUID:
  BLE.setLocalName("Nano 33 BLE Sense Orange");
  BLE.setAdvertisedService(ledService);

  // add the characteristic to the service
  ledService.addCharacteristic(switchCharacteristic);

  // add service
  BLE.addService(ledService);


  unsigned long moveTime = 0xDEADBEEF;
  for (int i = 0; i < 4; i++) {
    switchCharacteristic.writeValue((uint8_t)(moveTime >> (i * 8)));
  }

  // start advertising
  BLE.advertise();

  Serial.println("BLE LED Peripheral Orange");
}

void loop() {
  // listen for Bluetooth® Low Energy peripherals to connect:
  BLEDevice central = BLE.central();

  // if a central is connected to peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    // print the central's MAC address:
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, HIGH);            // turn on the LED to indicate the connection

    // while the central is still connected to peripheral:
    while (central.connected()) {
      // if the remote device wrote to the characteristic,
      // use the value to control the LED:
      if (switchCharacteristic.written()) {
        switch (switchCharacteristic.value()) {   // any value other than 0
          case 01:
            Serial.println("Red LED on");
            digitalWrite(LEDR, LOW);            // will turn the LED on
            digitalWrite(LEDG, HIGH);         // will turn the LED off
            digitalWrite(LEDB, HIGH);         // will turn the LED off
            break;
          case 02:
            Serial.println("Green LED on");
            digitalWrite(LEDR, HIGH);         // will turn the LED off
            digitalWrite(LEDG, LOW);        // will turn the LED on
            digitalWrite(LEDB, HIGH);        // will turn the LED off
            break;
          case 03:
            Serial.println("Blue LED on");
            digitalWrite(LEDR, HIGH);         // will turn the LED off
            digitalWrite(LEDG, HIGH);       // will turn the LED off
            digitalWrite(LEDB, LOW);         // will turn the LED on
            break;
          default:
            Serial.println(F("LEDs off"));
            digitalWrite(LEDR, HIGH);          // will turn the LED off
            digitalWrite(LEDG, HIGH);        // will turn the LED off
            digitalWrite(LEDB, HIGH);         // will turn the LED off
            break;
        }
      }
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