from django.conf import settings
from django.test import TestCase, override_settings

from core.plugins import MachineValidationPluginManager
from service.mock import MockAccountDriver

# Create an instance
# build identical instance status history timings and try to add them
# It should fail and force you to do 'the right thing only'


@override_settings(
    BLACKLIST_METADATA_KEY="atmo_image_exclude",
    WHITELIST_METADATA_KEY="atmo_image_include"
)
class TestMachineMonitoring(TestCase):
    def tearDown(self):
        if getattr(self, 'account_driver', None):
            self.account_driver.clear_images()

    def setUp(self):
        self.account_driver = MockAccountDriver()
        self.account_driver.generate_images()
        x = 11
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.BLACKLIST_METADATA_KEY: "yes"
        }
        skip_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        x = 12
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.WHITELIST_METADATA_KEY: "yes"
        }
        allow_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        x = 13
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.WHITELIST_METADATA_KEY: "no"
        }
        no_allow_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        x = 14
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.BLACKLIST_METADATA_KEY: "no"
        }
        no_skip_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        x = 14
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.BLACKLIST_METADATA_KEY: "nopers"
        }
        invalid_skip_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        x = 15
        overrides = {
            "id": "deadbeef-dead-dead-beef-deadbeef%04d" % x,
            "name": "Test glance image %04d" % x,
            "application_name": "Test Application %04d" % x,
            "version_name": "v%d.0-test" % x,
            settings.WHITELIST_METADATA_KEY: "Yeppers"
        }
        invalid_allow_atmosphere_image = self.account_driver._generate_glance_image(
            **overrides
        )
        self.account_driver.glance_images.append(skip_atmosphere_image)
        self.account_driver.glance_images.append(allow_atmosphere_image)
        self.account_driver.glance_images.append(no_skip_atmosphere_image)
        self.account_driver.glance_images.append(no_allow_atmosphere_image)
        self.account_driver.glance_images.append(invalid_skip_atmosphere_image)
        self.account_driver.glance_images.append(invalid_allow_atmosphere_image)
        self.basic_validation = MachineValidationPluginManager.get_validator(
            self.account_driver,
            "atmosphere.plugins.machine_validation.BasicValidation"
        )
        self.cyverse_validation = MachineValidationPluginManager.get_validator(
            self.account_driver,
            "atmosphere.plugins.machine_validation.CyverseValidation"
        )
        self.whitelist_validation = MachineValidationPluginManager.get_validator(
            self.account_driver,
            "atmosphere.plugins.machine_validation.WhitelistValidation"
        )

    def test_monitoring_with_basic_validation(self):
        """
        Testing validation plugin: BasicValidation
        """
        validated_machines = []
        images = self.account_driver.list_images()
        for glance_image in images:
            if self.basic_validation.machine_is_valid(glance_image):
                validated_machines.append(glance_image)
        # Assert: validated_machines includes # machines, based on setUp.
        self.assertTrue(len(validated_machines) == len(images))

    def test_monitoring_with_cyverse_validation(self):
        """
        Testing validation plugin: CyverseValidation
        """
        validated_machines = []
        images = self.account_driver.list_images()
        for glance_image in images:
            if self.cyverse_validation.machine_is_valid(glance_image):
                validated_machines.append(glance_image)
        # All images _except_ 0011 should be included in validated machines...
        self.assertTrue(
            len(validated_machines) == len(images) - 1,
            "Invalid # of machines validated(%s) -- Expected %s" %
            (len(validated_machines), len(images) - 1)
        )
        # 0011 should NOT be in the list of validated machines, due to the 'skip_atmosphere' metadata on the image.
        self.assertEquals(
            [
                img for img in validated_machines
                if img.id == "deadbeef-dead-dead-beef-deadbeef0011"
            ], []
        )
        return

    def test_monitoring_with_whitelist_validation(self):
        """
        Testing validation plugin: WhitelistValidation
        """
        validated_machines = []
        images = self.account_driver.list_images()
        for glance_image in images:
            if self.whitelist_validation.machine_is_valid(glance_image):
                validated_machines.append(glance_image)
        # All images should be skipped _except_ 0012
        self.assertTrue(
            len(validated_machines) == 1,
            "Expected validated_machines(%s) to contain 1 element" %
            validated_machines
        )
        # 0012 should be in the list of validated machines,
        # due to the settings.BLACKLIST_METADATA_KEY metadata on the image.
        self.assertEquals(
            [
                img for img in validated_machines
                if img.id == "deadbeef-dead-dead-beef-deadbeef0011"
            ], []
        )
        return
