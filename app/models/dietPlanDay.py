class DietPlanDay:
    def __init__(self, meals):
        self.meals = meals

    def to_dict(self):
        return {
            'meals': self.meals,
        }
    