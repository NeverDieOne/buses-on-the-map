from dataclasses import dataclass, fields


class WindowBoundsValidationError(Exception):
    pass


@dataclass
class WindowBounds:
    south_lat: float = 0.0
    north_lat: float = 0.0
    west_lng: float = 0.0
    east_lng: float = 0.0

    def is_inside(self, lat, lng):
        return all([
            self.south_lat < lat < self.north_lat,
            self.west_lng < lng < self.east_lng
        ])

    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng

    @staticmethod
    def validate(message):
        errors = []
        message_data = message.get('data')
        message_type = message.get('msgType')

        if not message_data:
            errors.append('Data parameter is required')
        if not message_type:
            errors.append('msgType is required')
        
        if message_data:
            for field in fields(WindowBounds):
                field_name = field.name
                field_type = field.type

                if not message_data.get(field_name):
                    errors.append(f'{field_name} is required')
                else:
                    if not isinstance(message_data.get(field_name), field_type):
                        errors.append(f'{field_name} must be {field_type}')
        
        if errors:
            raise WindowBoundsValidationError(errors)
