# -*- coding: utf-8 -*-
"""
Module for the Tinkerforge Barometer Bricklet 2.0
(https://www.tinkerforge.com/en/doc/Hardware/Bricklets/Barometer_V2.html)
implemented using Python AsyncIO. It does the low-lvel communication with the
Tinkerforge ip connection and also handles conversion of raw units to SI units.
"""
from collections import namedtuple
from decimal import Decimal
from enum import Enum, unique

from .devices import DeviceIdentifier, BrickletWithMCU, ThresholdOption
from .ip_connection_helper import pack_payload, unpack_payload

GetAirPressureCallbackConfiguration = namedtuple('AirPressureCallbackConfiguration', ['period', 'value_has_to_change', 'option', 'min', 'max'])
GetAltitudeCallbackConfiguration = namedtuple('AltitudeCallbackConfiguration', ['period', 'value_has_to_change', 'option', 'min', 'max'])
GetTemperatureCallbackConfiguration = namedtuple('TemperatureCallbackConfiguration', ['period', 'value_has_to_change', 'option', 'min', 'max'])
GetMovingAverageConfiguration = namedtuple('MovingAverageConfiguration', ['moving_average_length_air_pressure', 'moving_average_length_temperature'])
GetCalibration = namedtuple('Calibration', ['measured_air_pressure', 'actual_air_pressure'])
GetSensorConfiguration = namedtuple('SensorConfiguration', ['data_rate', 'air_pressure_low_pass_filter'])


@unique
class CallbackID(Enum):
    """
    The callbacks available to this bricklet
    """
    AIR_PRESSURE = 4
    ALTITUDE = 8
    TEMPERATURE = 12


@unique
class FunctionID(Enum):
    """
    The function calls available to this bricklet
    """
    GET_AIR_PRESSURE = 1
    SET_AIR_PRESSURE_CALLBACK_CONFIGURATION = 2
    GET_AIR_PRESSURE_CALLBACK_CONFIGURATION = 3
    GET_ALTITUDE = 5
    SET_ALTITUDE_CALLBACK_CONFIGURATION = 6
    GET_ALTITUDE_CALLBACK_CONFIGURATION = 7
    GET_TEMPERATURE = 9
    SET_TEMPERATURE_CALLBACK_CONFIGURATION = 10
    GET_TEMPERATURE_CALLBACK_CONFIGURATION = 11
    SET_MOVING_AVERAGE_CONFIGURATION = 13
    GET_MOVING_AVERAGE_CONFIGURATION = 14
    SET_REFERENCE_AIR_PRESSURE = 15
    GET_REFERENCE_AIR_PRESSURE = 16
    SET_CALIBRATION = 17
    GET_CALIBRATION = 18
    SET_SENSOR_CONFIGURATION = 19
    GET_SENSOR_CONFIGURATION = 20


@unique
class DataRate(Enum):
    """
    Supported data rates of the air pressure sensor
    """
    OFF = 0
    RATE_1HZ = 1
    RATE_10HZ = 2
    RATE_25HZ = 3
    RATE_50HZ = 4
    RATE_75HZ = 5


@unique
class LowPassFilter(Enum):
    """
    Low pass filter options of the pressure sensor
    """
    FILTER_OFF = 0
    FILTER_9TH = 1
    FILTER_20TH = 2


class BrickletBarometerV2(BrickletWithMCU):
    """
    Measures air pressure and altitude changes
    """
    DEVICE_IDENTIFIER = DeviceIdentifier.BRICKLET_BAROMETER_V2
    DEVICE_DISPLAY_NAME = 'Barometer Bricklet 2.0'

    # Convenience imports, so that the user does not need to additionally import them
    CallbackID = CallbackID
    FunctionID = FunctionID
    ThresholdOption = ThresholdOption
    DataRate = DataRate
    LowPassFilter = LowPassFilter

    CALLBACK_FORMATS = {
        CallbackID.AIR_PRESSURE: 'i',
        CallbackID.ALTITUDE: 'i',
        CallbackID.TEMPERATURE: 'i',
    }

    def __init__(self, uid, ipcon):
        """
        Creates an object with the unique device ID *uid* and adds it to
        the IP Connection *ipcon*.
        """
        super().__init__(self.DEVICE_DISPLAY_NAME, uid, ipcon)

        self.api_version = (2, 0, 0)

    async def get_air_pressure(self):
        """
        Returns the measured air pressure.


        If you want to get the value periodically, it is recommended to use the
        :cb:`Air Pressure` callback. You can set the callback configuration
        with :func:`Set Air Pressure Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_AIR_PRESSURE,
            response_expected=True
        )
        return self.__air_pressure_sensor_to_si(unpack_payload(payload, 'i'))

    async def set_air_pressure_callback_configuration(self, period=0, value_has_to_change=False, option=ThresholdOption.OFF, minimum=0, maximum=0, response_expected=True):  # pylint: disable=too-many-arguments
        """
        The period is the period with which the :cb:`Air Pressure` callback is triggered
        periodically. A value of 0 turns the callback off.

        If the `value has to change`-parameter is set to true, the callback is only
        triggered after the value has changed. If the value didn't change
        within the period, the callback is triggered immediately on change.

        If it is set to false, the callback is continuously triggered with the period,
        independent of the value.

        It is furthermore possible to constrain the callback with thresholds.

        The `option`-parameter together with min/max sets a threshold for the :cb:`Air Pressure` callback.

        The following options are possible:

        .. csv-table::
         :header: "Option", "Description"
         :widths: 10, 100

         "'x'",    "Threshold is turned off"
         "'o'",    "Threshold is triggered when the value is *outside* the min and max values"
         "'i'",    "Threshold is triggered when the value is *inside* or equal to the min and max values"
         "'<'",    "Threshold is triggered when the value is smaller than the min value (max is ignored)"
         "'>'",    "Threshold is triggered when the value is greater than the min value (max is ignored)"

        If the option is set to 'x' (threshold turned off) the callback is triggered with the fixed period.
        """
        option = ThresholdOption(option)
        assert period >= 0
        assert minimum >= 0
        assert maximum >= 0

        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_AIR_PRESSURE_CALLBACK_CONFIGURATION,
            data=pack_payload(
              (
                int(period),
                bool(value_has_to_change),
                option.value.encode('ascii'),
                self.__si_to_air_pressure_sensor(minimum),
                self.__si_to_air_pressure_sensor(maximum),
              ), 'I ! c i i'),
            response_expected=response_expected
        )

    async def get_air_pressure_callback_configuration(self):
        """
        Returns the callback configuration as set by :func:`Set Air Pressure Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_AIR_PRESSURE_CALLBACK_CONFIGURATION,
            response_expected=True
        )
        period, value_has_to_change, option, minimum, maximum = unpack_payload(payload, 'I ! c i i')
        option = ThresholdOption(option)
        minimum, maximum = self.__air_pressure_sensor_to_si(minimum), self.__air_pressure_sensor_to_si(maximum)
        return GetAirPressureCallbackConfiguration(period, value_has_to_change, option, minimum, maximum)

    async def get_altitude(self):
        """
        Returns the relative altitude of the air pressure sensor. The value
        is calculated based on the difference between the
        current air pressure and the reference air pressure that can be set
        with :func:`Set Reference Air Pressure`.


        If you want to get the value periodically, it is recommended to use the
        :cb:`Altitude` callback. You can set the callback configuration
        with :func:`Set Altitude Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_ALTITUDE,
            response_expected=True
        )
        return self.__altitude_sensor_to_si(unpack_payload(payload, 'i'))

    async def set_altitude_callback_configuration(self, period=0, value_has_to_change=False, option=ThresholdOption.OFF, minimum=0, maximum=0, response_expected=True):  # pylint: disable=too-many-arguments
        """
        The period is the period with which the :cb:`Altitude` callback is triggered
        periodically. A value of 0 turns the callback off.

        If the `value has to change`-parameter is set to true, the callback is only
        triggered after the value has changed. If the value didn't change
        within the period, the callback is triggered immediately on change.

        If it is set to false, the callback is continuously triggered with the period,
        independent of the value.

        It is furthermore possible to constrain the callback with thresholds.

        The `option`-parameter together with min/max sets a threshold for the :cb:`Altitude` callback.

        The following options are possible:

        .. csv-table::
         :header: "Option", "Description"
         :widths: 10, 100

         "'x'",    "Threshold is turned off"
         "'o'",    "Threshold is triggered when the value is *outside* the min and max values"
         "'i'",    "Threshold is triggered when the value is *inside* or equal to the min and max values"
         "'<'",    "Threshold is triggered when the value is smaller than the min value (max is ignored)"
         "'>'",    "Threshold is triggered when the value is greater than the min value (max is ignored)"

        If the option is set to 'x' (threshold turned off) the callback is triggered with the fixed period.
        """
        option = ThresholdOption(option)
        assert period >= 0

        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_ALTITUDE_CALLBACK_CONFIGURATION,
            data=pack_payload(
              (
                int(period),
                bool(value_has_to_change),
                option.value.encode('ascii'),
                self.__si_to_altitude_sensor(minimum),
                self.__si_to_altitude_sensor(maximum)
              ), 'I ! c i i'),
            response_expected=response_expected
        )

    async def get_altitude_callback_configuration(self):
        """
        Returns the callback configuration as set by :func:`Set Altitude Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_ALTITUDE_CALLBACK_CONFIGURATION,
            response_expected=True
        )
        period, value_has_to_change, option, minimum, maximum = unpack_payload(payload, 'I ! c i i')
        option = ThresholdOption(option)
        minimum, maximum = self.__altitude_sensor_to_si(minimum), self.__altitude_sensor_to_si(maximum)
        return GetAltitudeCallbackConfiguration(period, value_has_to_change, option, minimum, maximum)

    async def get_temperature(self):
        """
        Returns the temperature of the air pressure sensor.

        This temperature is used internally for temperature compensation
        of the air pressure measurement. It is not as accurate as the
        temperature measured by the :ref:`temperature_v2_bricklet` or the
        :ref:`temperature_ir_v2_bricklet`.


        If you want to get the value periodically, it is recommended to use the
        :cb:`Temperature` callback. You can set the callback configuration
        with :func:`Set Temperature Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_TEMPERATURE,
            response_expected=True
        )
        return self.__temperature_sensor_to_si(unpack_payload(payload, 'i'))

    async def set_temperature_callback_configuration(self, period=0, value_has_to_change=False, option=ThresholdOption.OFF, minimum=0, maximum=0, response_expected=True):  # pylint: disable=too-many-arguments
        """
        The period is the period with which the :cb:`Temperature` callback is triggered
        periodically. A value of 0 turns the callback off.

        If the `value has to change`-parameter is set to true, the callback is only
        triggered after the value has changed. If the value didn't change
        within the period, the callback is triggered immediately on change.

        If it is set to false, the callback is continuously triggered with the period,
        independent of the value.

        It is furthermore possible to constrain the callback with thresholds.

        The `option`-parameter together with min/max sets a threshold for the :cb:`Temperature` callback.

        The following options are possible:

        .. csv-table::
         :header: "Option", "Description"
         :widths: 10, 100

         "'x'",    "Threshold is turned off"
         "'o'",    "Threshold is triggered when the value is *outside* the min and max values"
         "'i'",    "Threshold is triggered when the value is *inside* or equal to the min and max values"
         "'<'",    "Threshold is triggered when the value is smaller than the min value (max is ignored)"
         "'>'",    "Threshold is triggered when the value is greater than the min value (max is ignored)"

        If the option is set to 'x' (threshold turned off) the callback is triggered with the fixed period.
        """
        option = ThresholdOption(option)
        assert period >= 0

        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_TEMPERATURE_CALLBACK_CONFIGURATION,
            data=pack_payload(
              (
                int(period),
                bool(value_has_to_change),
                option.value.encode('ascii'),
                self.__si_to_temperature_sensor(minimum),
                self.__si_to_temperature_sensor(maximum)
              ), 'I ! c i i'),
            response_expected=response_expected
        )

    async def get_temperature_callback_configuration(self):
        """
        Returns the callback configuration as set by :func:`Set Temperature Callback Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_ALTITUDE_CALLBACK_CONFIGURATION,
            response_expected=True
        )
        period, value_has_to_change, option, minimum, maximum = unpack_payload(payload, 'I ! c i i')
        option = ThresholdOption(option)
        minimum, maximum = self.__temperature_sensor_to_si(minimum), self.__temperature_sensor_to_si(maximum)
        return GetTemperatureCallbackConfiguration(period, value_has_to_change, option, minimum, maximum)

    async def set_moving_average_configuration(self, moving_average_length_air_pressure=100, moving_average_length_temperature=100, response_expected=True):
        """
        Sets the length of a `moving averaging <https://en.wikipedia.org/wiki/Moving_average>`__
        for the air pressure and temperature measurements.

        Setting the length to 1 will turn the averaging off. With less
        averaging, there is more noise on the data.

        If you want to do long term measurements the longest moving average will give
        the cleanest results.
        """
        assert moving_average_length_air_pressure >= 1
        assert moving_average_length_temperature >= 1

        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_MOVING_AVERAGE_CONFIGURATION,
            data=pack_payload(
              (
                int(moving_average_length_air_pressure),
                int(moving_average_length_temperature),
              ), 'H H'),
            response_expected=response_expected
        )

    async def get_moving_average_configuration(self):
        """
        Returns the moving average configuration as set by
        :func:`Set Moving Average Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_MOVING_AVERAGE_CONFIGURATION,
            response_expected=True
        )

        return GetMovingAverageConfiguration(*unpack_payload(payload, 'H H'))

    async def set_reference_air_pressure(self, air_pressure=1013.250, response_expected=True):
        """
        Sets the reference air pressure for the altitude calculation.
        Setting the reference to the
        current air pressure results in a calculated altitude of 0mm. Passing 0 is
        a shortcut for passing the current air pressure as reference.

        Well known reference values are the Q codes
        `QNH <https://en.wikipedia.org/wiki/QNH>`__ and
        `QFE <https://en.wikipedia.org/wiki/Mean_sea_level_pressure#Mean_sea_level_pressure>`__
        used in aviation.
        """
        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_REFERENCE_AIR_PRESSURE,
            data=pack_payload(
              (
                self.__si_to_air_pressure_sensor(air_pressure),
              ), 'i'),
            response_expected=response_expected
        )

    async def get_reference_air_pressure(self):
        """
        Returns the reference air pressure as set by :func:`Set Reference Air Pressure`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_REFERENCE_AIR_PRESSURE,
            response_expected=True
        )

        return self.__air_pressure_sensor_to_si(unpack_payload(payload, 'i'))

    async def set_calibration(self, measured_air_pressure, actual_air_pressure, response_expected=True):
        """
        Sets the one point calibration (OPC) values for the air pressure measurement.

        Before the Bricklet can be calibrated any previous calibration has to be removed
        by setting ``measured air pressure`` and ``actual air pressure`` to 0.

        Then the current air pressure has to be measured using the Bricklet
        (``measured air pressure``) and with an accurate reference barometer
        (``actual air pressure``) at the same time and passed to this function.

        After proper calibration the air pressure measurement can achieve an accuracy
        up to 0.2 hPa.

        The calibration is saved in the EEPROM of the Bricklet and only needs to be
        configured once.
        """
        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_CALIBRATION,
            data=pack_payload(
              (
                self.__si_to_air_pressure_sensor(measured_air_pressure),
                self.__si_to_air_pressure_sensor(actual_air_pressure),
              ), 'i i'),
            response_expected=response_expected
        )

    async def get_calibration(self):
        """
        Returns the air pressure one point calibration values as set by
        :func:`Set Calibration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_CALIBRATION,
            response_expected=True
        )
        measured_air_pressure, actual_air_pressure = unpack_payload(payload, 'i i')
        measured_air_pressure, actual_air_pressure = self.__air_pressure_sensor_to_si(measured_air_pressure), self.__air_pressure_sensor_to_si(actual_air_pressure)

        return GetCalibration(measured_air_pressure, actual_air_pressure)

    async def set_sensor_configuration(self, data_rate=DataRate.RATE_50HZ, air_pressure_low_pass_filter=LowPassFilter.FILTER_9TH, response_expected=True):
        """
        Configures the data rate and air pressure low pass filter. The low pass filter
        cut-off frequency (if enabled) can be set to 1/9th or 1/20th of the configure
        data rate to decrease the noise on the air pressure data.

        The low pass filter configuration only applies to the air pressure measurement.
        There is no low pass filter for the temperature measurement.

        A higher data rate will result in a less precise temperature because of
        self-heating of the sensor. If the accuracy of the temperature reading is
        important to you, we would recommend the 1Hz data rate.
        """
        if not isinstance(data_rate, DataRate):
            data_rate = DataRate(data_rate)
        if not isinstance(air_pressure_low_pass_filter, LowPassFilter):
            air_pressure_low_pass_filter = LowPassFilter(air_pressure_low_pass_filter)

        await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.SET_SENSOR_CONFIGURATION,
            data=pack_payload(
              (
                data_rate.value,
                air_pressure_low_pass_filter.value,
              ), 'B B'),
            response_expected=response_expected
        )

    async def get_sensor_configuration(self):
        """
        Returns the sensor configuration as set by :func:`Set Sensor Configuration`.
        """
        _, payload = await self.ipcon.send_request(
            device=self,
            function_id=FunctionID.GET_SENSOR_CONFIGURATION,
            response_expected=True
        )
        data_rate, air_pressure_low_pass_filter = unpack_payload(payload, 'B B')
        data_rate, air_pressure_low_pass_filter = DataRate(data_rate), LowPassFilter(air_pressure_low_pass_filter)

        return GetSensorConfiguration(data_rate, air_pressure_low_pass_filter)

    @staticmethod
    def __air_pressure_sensor_to_si(value):
        """
        Convert the sensor value to SI units
        """
        return Decimal(value) / 1000

    @staticmethod
    def __si_to_air_pressure_sensor(value):
        """
        Convert SI units to raw values
        """
        return int(value * 1000)

    @staticmethod
    def __altitude_sensor_to_si(value):
        """
        Convert the sensor value to SI units
        """
        return Decimal(value) / 1000

    @staticmethod
    def __si_to_altitude_sensor(value):
        """
        Convert SI units to raw values
        """
        return int(value * 1000)

    @staticmethod
    def __temperature_sensor_to_si(value):
        """
        Convert the sensor value to SI units
        """
        return Decimal(value) / 100

    @staticmethod
    def __si_to_temperature_sensor(value):
        """
        Convert SI units to raw values
        """
        return int(value * 100)

    def _process_callback_payload(self, header, payload):
        if header['function_id'] is CallbackID.AIR_PRESSURE:  # pylint: disable=no-else-return
            payload = unpack_payload(payload, self.CALLBACK_FORMATS[header['function_id']])
            header['sid'] = 0
            result = self.__air_pressure_sensor_to_si(payload), True    # payload, done
        elif header['function_id'] is CallbackID.ALTITUDE:
            payload = unpack_payload(payload, self.CALLBACK_FORMATS[header['function_id']])
            header['sid'] = 1
            result = self.__altitude_sensor_to_si(payload), True    # payload, done
        else:
            payload = unpack_payload(payload, self.CALLBACK_FORMATS[header['function_id']])
            header['sid'] = 2
            result = self.__temperature_sensor_to_si(payload), True    # payload, done
        return result
