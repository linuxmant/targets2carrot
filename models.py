from typing import Collection

ION_MODES = ['positive', 'negative']
ION_MODES = {
    'positive': ['positive', 'pos', 'p', '+'],
    'negative': ['negative', 'neg', 'n', '-']
}

TARGET_TYPES = {'istd': 'ISTD', 'manual': 'MANUAL_COMPOUND', 'validation': 'VALIDATION'}


class Target:
    identifier: str
    accurateMass: float
    adduct: str
    retentionTime: float
    retentionTimeUnit: str
    inchikey: str
    isInternalStandard: bool
    type: str
    msms: str

    def __init__(self, name, mz, rt, msms, rt_unit, adduct, inchikey, tgt_type):
        self.identifier: str = name.strip() if name is not None else None
        self.accurateMass: float = mz
        self.adduct: str = adduct.strip() if adduct is not None else None
        self.retentionTime: float = rt
        self.retentionTimeUnit: str = rt_unit.strip()
        self.inchikey: str = inchikey.strip() if inchikey is not None else None
        self.isInternalStandard: bool = tgt_type.lower() == 'istd'
        self.type: str = TARGET_TYPES.get(tgt_type.lower())
        self.msms: str = msms.strip() if msms is not None else None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def from_dict(target: dict):
        return Target(name=target.get('name', target.get('identifier')), mz=target['accurateMass'],
                      rt=target['retentionTime'], rt_unit=target.get('retentionTimeUnit', 'minutes'),
                      msms=target.get('msms', None), adduct=target.get('adduct', None), inchikey=target.get('inchikey', None),
                      tgt_type=target.get('type', target.get('target_type', 'istd')))

    def to_csv(self) -> list:
        return [self.identifier, self.accurateMass, self.adduct, self.retentionTime,
                self.retentionTimeUnit, self.type, self.inchikey, self.confirmed, self.msms]


class Config:
    name: str
    instrument: str
    column: str
    ionMode: str
    targets: Collection[Target]

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
    config: Config

    def __init__(self, config):
        if isinstance(config, Config):
            self.config = config
        else:
            targets = [Target.from_dict(t) for t in config['targets']]

            self.config = Config(config['name'], config['instrument'], targets, config['column'],
                                 config.get('ionMode', config.get('ion_mode')))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return str(self.__dict__)
