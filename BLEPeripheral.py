import simplepyble

class BLEPeripheral:
    def __init__(self, address):
        self.address = address
        self.peripheral = None

        # Connect to the peripheral
        try:
            adapters = simplepyble.Adapter.get_adapters()

            if len(adapters) == 0:
                print("No adapters found")
            elif len(adapters) == 1:
                adapter = adapters[0]
        
            adapter.set_callback_on_scan_start(lambda: print("Scan started."))
            adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))
            # Scan for 5 seconds
            adapter.scan_for(2000)
            peripherals = adapter.scan_get_results()

            add_found = False
            for p in peripherals:
                if p.address() == address:
                    self.peripheral = p
                    add_found = True

            if not add_found:
                print(f"Error! Peripheral with address {address} not found.")
                self.peripheral = None
            
        except Exception as e:
            print(f"Error: Could not connect to peripheral at address {address}.")
            print(e)


    def connect(self):
        self.peripheral.connect()

    def disconnect(self):
        if self.peripheral:
            self.peripheral.disconnect()
            return 1
        return 0

    def read(self, service_uuid, char_uuid, bytes = 1):
        if self.peripheral:
            try:
                return self.peripheral.read(service_uuid, char_uuid)
            except Exception as e:
                # print("Error reading from peripheral device.")
                # print(e)
                return None

    def write(self, service_uuid, char_uuid, bits):
        if self.peripheral:
            self.peripheral.write_request(service_uuid, char_uuid, bits)

    def read_until_found(self, service_uuid, char_uuid, value, timeout = 5, dt = 0.1):
        if self.peripheral:
            return 0
