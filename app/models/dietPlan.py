from models.dietPlanDay import DietPlanDay
from typing import List

import datetime

class DietPlan:
    def __init__(self, name, description, image_url, user_id,daydietplans: List[DietPlanDay]):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.user_id = user_id
        self.daydietplans = daydietplans
        self.creation_time = str(datetime.datetime.utcnow().timestamp())

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'user_id': self.user_id,
            'daydietplans':self.daydietplans,
        }

