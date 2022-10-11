from enum import Enum
from typing import Collection

ION_MODES = {
    'positive': ['positive', 'pos', 'p', '+'],
    'negative': ['negative', 'neg', 'n', '-']
}

TARGET_TYPES = {'istd': 'ISTD', 'manual': 'MANUAL_COMPOUND'}


class Target:
    def __init__(self, name, mz, rt, msms, rt_unit,
                 adduct, inchikey, tgt_type, origin,
                 is_istd, is_required=False, is_confirmed=True, zone=None):
        self.identifier: str = name.strip()
        self.accurateMass: float = mz
        self.retentionTime: float = rt
        self.retentionTimeUnit: str = rt_unit.strip()
        self.inchikey: str = inchikey.strip()
        self.adduct: str = adduct.strip()
        self.isInternalStandard: bool = is_istd
        self.requiredForCorrection: bool = is_required
        self.confirmed: bool = is_confirmed
        self.msms: str = msms.strip()
        self.type: str = TARGET_TYPES.get(tgt_type.lower())
        self.origin: str = origin
        self.zone: int = zone

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
        self.ion_mode: str = mode
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
