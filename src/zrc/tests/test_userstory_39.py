"""
Test the flow described in https://github.com/VNG-Realisatie/gemma-zaken/issues/39
"""
from rest_framework.test import APITestCase


class US39TestCase(APITestCase):

    def test_create_zaak(self):
        # read/parse OAS 3.0 spec
        # extract the operations & fill in the data
        raise NotImplementedError
