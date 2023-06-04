class CatalogError(Exception):
    pass


class InvalidAssetIdError(CatalogError):
    pass


class InvalidAttributeError(CatalogError):
    pass
