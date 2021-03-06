# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# DO NOT EDIT THIS FILE!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock, Mock, call

from test.utils import sleep, MockRPi, clock_pin, patcher

patcher.start()


class TestButton(TestCase):
    PIN = 25
    BOUNCETIME = 20

    def setUp(self):
        from datacom.week02 import Button
        MockRPi.GPIO.reset_mock()
        self.uut = Button(self.PIN, self.BOUNCETIME)

    @patch("datacom.week01.Button.__init__")
    def test_init(self, mock_super):
        from datacom.week01 import Button as BaseButton
        from datacom.week02 import Button
        btn = Button(self.PIN)
        assert isinstance(btn, BaseButton), "Invalid class inheritance"
        mock_super.assert_called_once_with(self.PIN), "Missing call to superclass init"
        assert self.uut._bouncetime == self.BOUNCETIME, "Bouncetime member variable not set correctly"

    def test_wait_for_press(self):
        self.uut.wait_for_press(1)
        MockRPi.GPIO.wait_for_edge.assert_called_once_with(self.PIN, MockRPi.GPIO.RISING, timeout=1)
        MockRPi.GPIO.reset_mock()
        self.uut.wait_for_press(10)
        MockRPi.GPIO.wait_for_edge.assert_called_once_with(self.PIN, MockRPi.GPIO.RISING, timeout=10)
        MockRPi.GPIO.reset_mock()
        MockRPi.GPIO.input.side_effect = clock_pin
        self.uut.wait_for_press()
        MockRPi.GPIO.wait_for_edge.assert_called_once_with(self.PIN, MockRPi.GPIO.RISING, timeout=None)

    def test_on_press(self):
        cb = Mock()
        MockRPi.GPIO.reset_mock()
        # MockRPi.GPIO.input.side_effect = clock_pin
        self.uut.on_press(cb)
        # MockRPi.GPIO.add_event_detect.assert_called_once_with(self.PIN, MockRPi.GPIO.RISING)
        MockRPi.GPIO.add_event_detect.assert_called_once()
        # cb.assert_called()        # TODO: figure out

    def test_on_release(self):
        cb = Mock()
        MockRPi.GPIO.reset_mock()
        # MockRPi.GPIO.input.side_effect = clock_pin
        self.uut.on_press(cb)
        MockRPi.GPIO.add_event_detect.assert_called_once()
        # cb.assert_called()


ButtonMock = MagicMock()


@patch('time.sleep', sleep)
@patch('datacom.week02.Button', ButtonMock)
class TestDemoButton(TestCase):
    def test_demo_button(self):
        from datacom.week02 import demo_button
        demo_button()
        assert call(20, 20) in ButtonMock.call_args_list, "btn1 not setup correctly"
        assert call(21, 20) in ButtonMock.call_args_list, "btn2 not setup correctly"


class TestLED(TestCase):
    PIN = 20
    BRIGHTNESS = 75

    def setUp(self):
        from datacom.week02 import LED
        MockRPi.GPIO.reset_mock()
        self.uut = LED(self.PIN, self.BRIGHTNESS)

    @patch("datacom.week01.LED.__init__")
    def test_init(self, mock_super):
        from datacom.week01 import LED as BaseLED
        from datacom.week02 import LED
        assert self.uut._brightness == self.BRIGHTNESS, "Brightness member variable set incorrectly"
        self.assertEqual(self.uut._pwm, MockRPi.GPIO.PWM(), "PWM protected member variable not set correctly")
        assert MockRPi.GPIO.PWM.call_args_list[0] == call(self.PIN, 1000), "PWM object not setup correctly"
        self.uut._pwm.start.assert_called_once_with(0), "Missing call to start PWM object"
        MockRPi.reset_mock()
        led = LED(self.PIN)
        assert isinstance(led, BaseLED), "Invalid class inheritance"
        assert led._brightness == 100, "Brightness member variable default value incorrect"
        mock_super.assert_called_once_with(self.PIN), "Missing call to superclass init"

    def test_brightness(self):
        from datacom.week02 import LED
        self.assertIsInstance(LED.brightness, property, "LED.brightness is not a property")
        self.assertEqual(self.uut.brightness, self.BRIGHTNESS, "LED.brightness getter failed")
        MockRPi.reset_mock()
        self.uut.brightness = 34
        self.assertEqual(self.uut.brightness, 34, "LED.brightness setter failed")
        self.assertEqual(self.uut._brightness, 34, "LED.brightness setter failed")
        self.uut._pwm.ChangeDutyCycle.assert_called_once_with(34)

    def test_on(self):
        MockRPi.reset_mock()
        self.uut.on()
        self.uut._pwm.start.assert_called_once_with(self.BRIGHTNESS), "Missing call to start PWM object"

    def test_off(self):
        self.uut.off()
        self.uut._pwm.stop.assert_called_once_with(), "Missing call to stop PWM object"

    def test_del(self):
        from datacom.week02 import LED
        led = LED(self.PIN)
        del led
        self.uut._pwm.stop.assert_called_once_with(), "Missing call to stop PWM object"


class TestRGBLED(TestCase):
    PINS = 11, 12, 13
    BRIGHTNESS = 75

    def setUp(self):
        from datacom.week02 import RGBLED
        MockRPi.GPIO.reset_mock()
        self.uut = RGBLED(*self.PINS)

    def test_init(self):
        from datacom.week02 import LED
        self.assertIsInstance(self.uut.red, LED, "RGBLED.red is not a LED object")
        self.assertIsInstance(self.uut.blue, LED, "RGBLED.blue is not a LED object")
        self.assertIsInstance(self.uut.green, LED, "RGBLED.green is not a LED object")

    def test_set_color(self):
        r, g, b = 100, 50, 255
        self.uut.set_color(r, g, b)
        self.assertEqual(self.uut.red.brightness, r / 255 * 100)
        self.assertEqual(self.uut.green.brightness, g / 255 * 100)
        self.assertEqual(self.uut.blue.brightness, b / 255 * 100)


class TestLEDBar(TestCase):
    PINS = 11, 12, 13, 14, 15

    def setUp(self):
        from datacom.week02 import LEDBar
        MockRPi.GPIO.reset_mock()
        self.uut = LEDBar(*self.PINS)

    def test_init(self):
        from datacom.week02 import LED
        assert all(isinstance(obj, LED) for obj in self.uut.leds), "member leds not initialized with LED objects"
        self.assertListEqual(list(self.PINS), [obj.pin for obj in self.uut.leds])

    def test_set_value(self):
        with self.assertRaises(ValueError):
            self.uut.set_value(7)
        with self.assertRaises(ValueError):
            self.uut.set_value(-1)

        for i in range(len(self.PINS)):
            self.uut.leds[0]._pwm.reset_mock()
            self.uut.set_value(i)
            self.assertEqual(self.uut.leds[0]._pwm.start.call_count, i,
                             "incorrect number of leds switched on for value {}".format(i))
            self.assertEqual(self.uut.leds[0]._pwm.stop.call_count, len(self.PINS) - i,
                             "incorrect number of leds switched off for value {}".format(i))

    def test_set_percent(self):
        with self.assertRaises(ValueError):
            self.uut.set_value(-10)
        with self.assertRaises(ValueError):
            self.uut.set_value(211)

        for i in range(0, 100, 10):
            self.uut.leds[0]._pwm.reset_mock()
            self.uut.set_percent(i)
            self.assertEqual(self.uut.leds[0]._pwm.start.call_count, round(i / 100 * len(self.PINS)),
                             "incorrect number of leds switched on for percentage {}".format(i))
            self.assertEqual(self.uut.leds[0]._pwm.stop.call_count, len(self.PINS) - round(i / 100 * len(self.PINS)),
                             "incorrect number of leds switched off percentage {}".format(i))


def teardownModule():
    patcher.stop()


if __name__ == '__main__':
    unittest.main()
