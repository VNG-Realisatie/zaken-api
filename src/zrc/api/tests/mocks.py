from zds_schema.constants import VertrouwelijkheidsAanduiding
from zds_schema.mocks import ZTCMockClient


class VertrouwelijkheidAanduidingZTCMockClient(ZTCMockClient):
    data = {
        'zaaktype': [{
            'url': 'https://ztc.nl/zaaktype/123',
            'vertrouwelijkheidaanduiding': VertrouwelijkheidsAanduiding.zaakvertrouwelijk,
        }]
    }

    @classmethod
    def from_url(cls, detail_url: str):
        return VertrouwelijkheidAanduidingZTCMockClient()
