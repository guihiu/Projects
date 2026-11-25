from datetime import datetime
class person:
    def __init__(self,id_person:int, name:str, phone:int):
        self.id_person=id_person
        self.name=name
        self.phone=phone

    def get_id(self):
        return self.id_person

class agenda:
    def __init__(self, id:int, data:datetime, id_person:int):
        self.id=id
        self.data=data
        self.id_person=id_person
