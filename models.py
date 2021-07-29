from typing import Collection

ION_MODES = ['posotive', 'negative']


class Target:
    def __init__(self, name, mz, rt, msms, rt_unit='minutes',
                 is_istd=True, is_required=False, is_confirmed=True, zone=0,
                 adduct=None, inchikey=None):
        self.identifier = name.strip(" ") if adduct is None else name.strip(" ") + ' ' + adduct.strip(" ")
        self.accurateMass = mz
        self.retentionTime = rt
        self.retentionTimeUnit = rt_unit
        self.inchikey = inchikey
        self.adduct = adduct
        self.isInternalStandard = is_istd
        self.requiredForCorrection = is_required
        self.confirmed = is_confirmed
        self.msms = msms
        self.zone = zone

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)


class Config:
    def __init__(self, name, instrument, targets: Collection[Target], desc=None, column='test', mode='positive'):
        self.name = name
        self.description = desc if desc is not None else self.name + ' description'
        self.instrument = instrument
        self.column = column
        self.ion_mode = mode if mode in ION_MODES else 'positive'
        self.targets = targets

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)


class Library:
    def __init__(self, config: Config):
        self.config = config

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)
