from unittest.mock import patch


class ZaakInformatieObjectSyncMixin:
    def setUp(self):
        super().setUp()

        patcher_sync_create = patch("zrc.sync.signals.sync_create_zio")
        self.mocked_sync_create = patcher_sync_create.start()
        self.addCleanup(patcher_sync_create.stop)

        patcher_sync_delete = patch("zrc.sync.signals.sync_delete_zio")
        self.mocked_sync_delete = patcher_sync_delete.start()
        self.addCleanup(patcher_sync_delete.stop)


class ZaakContactMomentSyncMixin:
    def setUp(self):
        super().setUp()

        patcher_sync_create_zcm = patch(
            "zrc.sync.signals.sync_create_zaakcontactmoment"
        )
        self.mocked_sync_create_zcm = patcher_sync_create_zcm.start()
        self.addCleanup(patcher_sync_create_zcm.stop)

        patcher_sync_delete_zcm = patch(
            "zrc.sync.signals.sync_delete_zaakcontactmoment"
        )
        self.mocked_sync_delete_zcm = patcher_sync_delete_zcm.start()
        self.addCleanup(patcher_sync_delete_zcm.stop)


class ZaakVerzoekSyncMixin:
    def setUp(self):
        super().setUp()

        patcher_sync_create_zv = patch("zrc.sync.signals.sync_create_zaakverzoek")
        self.mocked_sync_create_zv = patcher_sync_create_zv.start()
        self.addCleanup(patcher_sync_create_zv.stop)

        patcher_sync_delete_zv = patch("zrc.sync.signals.sync_delete_zaakverzoek")
        self.mocked_sync_delete_zv = patcher_sync_delete_zv.start()
        self.addCleanup(patcher_sync_delete_zv.stop)


class SyncMixin(
    ZaakInformatieObjectSyncMixin, ZaakContactMomentSyncMixin, ZaakVerzoekSyncMixin
):
    pass
