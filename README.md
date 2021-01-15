# TinkerforgeAsync
This is a reimplementation of the Tinkerforge Python bindings ([original Python bindings](https://www.tinkerforge.com/en/doc/Software/API_Bindings_Python.html)) using Python 3 asyncio. The original bindings used threads to manage the blocking operations. A much cleaner implementation is possible using the *await* syntax from asyncio.

**Note: This API implementation is not an official Tinkerforge implementation. I am in no way affiliated with the Tinkerforge GmbH. Use at your own risk. If you find any bugs, please report them.**

# Supported Bricks/Bricklets
|Brick|Supported|Tested|Comments|
|--|--|--|--|
|[Master](https://www.tinkerforge.com/en/doc/Hardware/Bricks/Master_Brick.html)|:x:|  :x:| WIP |

|Bricklet|Supported|Tested|
|--|--|--|
|[Ambient Light 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Ambient_Light_V2.html)|:heavy_check_mark:|:heavy_check_mark:|
|[Ambient Light 3.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Ambient_Light_V3.html)|:x:|:x:|
|[Barometer](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Barometer.html)|:heavy_check_mark:|:x:|
|[Humidity](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Humidity.html)|:heavy_check_mark:|:heavy_check_mark:|
|[Humidity 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Humidity_V2.html)|:heavy_check_mark:|:heavy_check_mark:|
|[Industrial Dual Analog In Bricklet 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Industrial_Dual_Analog_In_V2.html)|:x:|:x:|
|[Moisture](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Moisture.html)|:heavy_check_mark:|:heavy_check_mark:|
|[PTC Bricklet](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/PTC.html)|:heavy_check_mark:|:x:|
|[PTC Bricklet 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/PTC_V2.html)|:heavy_check_mark:|:x:|
|[Segment Display 4x7 Bricklet](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Segment_Display_4x7.html)|:heavy_check_mark:|:heavy_check_mark:|
|[Segment Display 4x7 Bricklet 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Segment_Display_4x7_V2.html)|:x:|:x:|
|[Temperature](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Temperature.html)|:heavy_check_mark:|:heavy_check_mark:|
|[Temperature 2.0](https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Temperature_V2.html)|:heavy_check_mark:|:heavy_check_mark:|

# Changes made to the API
Some of the design choices of the original Tinkerforge API are overly complex. I therefore replaced them with a simpler and more intuitive approach. A list of things that were changed can be found below:
### Design Changes
- Only Python 3 is supported (3.5+)
 - Replaced threads with an async event loop
 - Completely rewritten how responses from bricks/bricklets work. All setters now have a *response_expected* parameter, which when set to true will make the function call either return *True* or raise an error. There are no *set_response_expected()* functions any more.

   Old style:
   ```python
   bricklet = BrickletHumidity(UID, ipcon)
   bricklet.set_response_expected(BrickletHumidity.FUNCTION_SET_HUMIDITY_CALLBACK_PERIOD, True)
   bricklet.set_humidity_callback_period(1000)
   ```
   New style:
   ```python
   bricklet = BrickletHumidity(UID, ipcon)
   result = await bricklet.set_humidity_callback_period(1000, response_expected=True)    # True if successful
   ```
 - Replaced all constants with Enums and enforced their use using assertions. This will allow beginners to spot their mistakes earlier and make the code more readable, including any debug output statements.

   Old style:
   ```python
   class BrickletHumidity(Device):
       FUNCTION_GET_HUMIDITY = 1
       FUNCTION_GET_ANALOG_VALUE = 2
       FUNCTION_SET_HUMIDITY_CALLBACK_PERIOD = 3
       FUNCTION_GET_HUMIDITY_CALLBACK_PERIOD = 4
       FUNCTION_SET_ANALOG_VALUE_CALLBACK_PERIOD = 5
       FUNCTION_GET_ANALOG_VALUE_CALLBACK_PERIOD = 6
       FUNCTION_SET_HUMIDITY_CALLBACK_THRESHOLD = 7
       FUNCTION_GET_HUMIDITY_CALLBACK_THRESHOLD = 8
       FUNCTION_SET_ANALOG_VALUE_CALLBACK_THRESHOLD = 9
       FUNCTION_GET_ANALOG_VALUE_CALLBACK_THRESHOLD = 10
       FUNCTION_SET_DEBOUNCE_PERIOD = 11
       FUNCTION_GET_DEBOUNCE_PERIOD = 12
       FUNCTION_GET_IDENTITY = 255
   ```

   New style:
   ```python
   class BrickletHumidity(Device):
       @unique
       class FunctionID(Enum):
           GET_HUMIDITY = 1
           GET_ANALOG_VALUE = 2
           SET_HUMIDITY_CALLBACK_PERIOD = 3
           GET_HUMIDITY_CALLBACK_PERIOD = 4
           SET_ANALOG_VALUE_CALLBACK_PERIOD = 5
           GET_ANALOG_VALUE_CALLBACK_PERIOD = 6
           SET_HUMIDITY_CALLBACK_THRESHOLD = 7
           GET_HUMIDITY_CALLBACK_THRESHOLD = 8
           SET_ANALOG_VALUE_CALLBACK_THRESHOLD = 9
           GET_ANALOG_VALUE_CALLBACK_THRESHOLD = 10
           SET_DEBOUNCE_PERIOD = 11
           GET_DEBOUNCE_PERIOD = 12
   ```
 - Moved from base58 encoded uids to integers
 - Moved from callbacks to queues in order to keep users out of the callback hell. It makes the code style more readable when using the *await* syntax anyway.
 - Payloads will now be decoded by the *Device* object and not by the *ip_connection* any more. This makes the code a lot more readable. To do so, the payload and decoded header will be handed to the device. It will then decode it, if possible, and pass it on to the queue.
 - If physical quantities are measured we will now return standard SI units, not some unexpected stuff like centi °C (Temperature Bricklet). To preserve the precision the Decimal package is used. The only exception to this rule is the use of °C for temperature. This is for convenience.
 - All callbacks now contain a timestamp (Unix timestamp) and the device uid.

   Example:
   ```python
   {'timestamp': 1525308878, 'uid': 30842, 'device_id': <DeviceIdentifier.BrickletHumidity: 27>, 'function_id': <CallbackID.humidity_reached: 15>, 'payload': Decimal('43.6')}
   ```

- #### [IP Connection](https://www.tinkerforge.com/en/doc/Software/IPConnection_Python.html#api)
   - *IPConnection.authenticate(_secret_)*: removed. This can now be done through connect()
   - *IPConnection.set_timeout/IPConnection.get_timeout*: Replaced by a property
   - *IPConnection.register_callback(_callback_id_, _function_)*: Replaced by register_queue()

- #### [Master Brick](https://www.tinkerforge.com/en/doc/Software/Bricks/Master_Brick_Python.html)
   - BrickMaster.set_wifi_configuration()/BrickMaster.get_wifi_configuration() will take/return all ips in natural order
