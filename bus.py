from dataclasses import dataclass, fields


class BusValidationError(Exception):
    pass


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str

    @staticmethod
    def validate(message):
        errors = []
        
        for field in fields(Bus):
            field_name = field.name
            field_type = field.type

            if not message.get(field_name):
                errors.append(f'{field_name} is required')
            else:
                if not isinstance(message.get(field_name), field_type):
                    errors.append(f'{field_name} must be {field_type}')
        
        if errors:
            raise BusValidationError(errors)
