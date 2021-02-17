#!/usr/bin/env python3

import argparse
import logging
import sys
import usb.core


class UsbDeviceMatcher:
    def __init__(self, properties, handler):
        self.properties = properties
        self.handler = handler

    def matches(self, candidate):
        for prop, value in self.properties.items():
            if prop not in candidate.__dict__ or candidate.__dict__[prop] != value:
                return False
            return True


class UsbDeviceFinder:
    SUPPORTED_DEVICES = [
        UsbDeviceMatcher(
            {"idVendor": 0x0A5C, "idProduct": 0x5832},
            lambda device: __import__("cv2").ControlVault2(device),
        ),
        UsbDeviceMatcher(
            {"idVendor": 0x0A5C, "idProduct": 0x5834},
            lambda device: __import__("cv2").ControlVault2(device),
        ),
        UsbDeviceMatcher(
            {"idVendor": 0x0A5C, "idProduct": 0x5842},
            lambda device: __import__("cv3").ControlVault3(device),
        ),
        UsbDeviceMatcher(
            {"idVendor": 0x0A5C, "idProduct": 0x5843},
            lambda device: __import__("cv3").ControlVault3(device),
        ),
    ]

    @classmethod
    def _dev_matcher(cls, device):
        for matcher in cls.SUPPORTED_DEVICES:
            if matcher.matches(device):
                return True
            return False

    @classmethod
    def _cls_matcher(cls, device):
        for matcher in cls.SUPPORTED_DEVICES:
            if matcher.matches(device):
                return matcher.handler(device)
            raise Exception(
                "Cannot find handler for device {:04X}:{:04X}".format(
                    dev.idVendor, dev.idProduct
                )
            )

    @classmethod
    def find(cls):
        logger = logging.getLogger(__name__)
        logger.info("Looking for supported device...")

        device = usb.core.find(custom_match=cls._dev_matcher)
        if device is None:
            raise Exception("Cannot find BCM device - check list of supported devices")
        logger.info("Found {:04X}:{:04X}".format(device.idVendor, device.idProduct))

        handler = cls._cls_matcher(device)
        logger.info("Handler {} ({})".format(handler.__class__.__name__, handler.NAME))
        return handler


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Control the NFC module in ControlVault 2/3."
    )
    parser.add_argument(
        "command", nargs="?", help="command to execute", choices=["on", "off", "reset"]
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity level. Can be repeated.",
    )

    args = parser.parse_args()

    if not args.command:
        parser.error("No command specified")

    if args.verbose == 0:
        LOG.setLevel(logging.INFO)
    elif args.verbose == 1:
        LOG.setLevel(logging.DEBUG)
    elif args.verbose >= 2:
        LOG.setLevel(logging.TRACE)

    handler = UsbDeviceFinder.find()
    if args.command == "on":
        LOG.info("Turning NFC on...")
        handler.turn_on()
        LOG.info("NFC should be turned on now!")
    elif args.command == "off":
        LOG.info("Turning NFC off...")
        handler.turn_off()
        LOG.info("NFC should be turned off now!")
    elif args.command == "reset":
        LOG.info("Resetting device...")
        handler.reset()
        LOG.info("NFC device has been reset!")
