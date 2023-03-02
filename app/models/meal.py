class Meal:
    def __init__(self, name, description, ingredients, instructions):
        self.name = name
        self.description = description
        self.ingredients = ingredients
        self.instructions = instructions

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
        }
    