from enum import Enum
from typing import Collection

ION_MODES = ['positive', 'negative']
ION_MODES = {
    'positive': ['positive', 'pos', 'p', '+'],
    'negative': ['negative', 'neg', 'n', '-']
}

TARGET_TYPES = {'istd': 'ISTD', 'manual': 'MANUAL_COMPOUND', 'validation': 'VALIDATION'}


class Target:
    def __init__(self, name, mz, rt, msms, rt_unit, adduct, inchikey, tgt_type, is_istd):
        self.identifier: str = name.strip()
        self.accurateMass: float = mz
        self.adduct: str = adduct.strip()
        self.retentionTime: float = rt
        self.retentionTimeUnit: str = rt_unit.strip()
        self.inchikey: str = inchikey.strip()
        self.isInternalStandard: bool = is_istd
        self.type: str = TARGET_TYPES.get(tgt_type.lower())
        self.msms: str = msms.strip() if msms is not None else None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)


class Config:
    def __init__(self, name: str, instrument: str, targets: Collection[Target], column: str = 'test',
                 mode: str = 'positive', desc: str = None):
        self.name: str = name
        # self.description = desc if desc is not None else ''
        self.instrument: str = instrument
        self.column: str = column
        self.ionMode: str = mode
        self.targets: Collection[Target] = targets

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)


class Library:
    def __init__(self, config: Config):
        self.config = [config]

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)
