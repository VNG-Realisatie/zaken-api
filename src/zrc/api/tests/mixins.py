from unittest.mock import patch


class ZaakInformatieObjectSyncMixin:

    def setUp(self):
        super().setUp()

        patcher_sync_create = patch('zrc.sync.signals.sync_create')
        self.mocked_sync_create = patcher_sync_create.start()
        self.addCleanup(patcher_sync_create.stop)

        patcher_sync_delete = patch('zrc.sync.signals.sync_delete')
        self.mocked_sync_delete = patcher_sync_delete.start()
        self.addCleanup(patcher_sync_delete.stop)
