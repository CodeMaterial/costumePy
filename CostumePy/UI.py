import logging


class UI:
    def __init__(self, node):

        self.elements = {}
        self.node = node

    def update(self):
        state = {}
        state["elements"] = {}
        for element_id in self.elements:
            new_id = "%02i_%s" % (self.elements[element_id]["order"], element_id)
            state["elements"][new_id] = self.elements[element_id]
            if not self.node.running:
                state["elements"][new_id]["enabled"] = False

        state["running"] = self.node.running
        self.node.broadcast("_UI_UPDATE", data=state)

    def add_text(self, element_id, text="None", text_class="", order=99):
        if element_id not in self.elements:
            self.elements[element_id] = {"type": "Text", "text": text, "text_class": text_class, "order": order}
        else:
            logging.error("Cannot create new UI element with id %s because it already exists" % element_id)
        return NotImplemented

    def add_button(self, element_id, text="Not Defined", topic=None, data=None, button_class="btn btn-default", order=99):
        if element_id not in self.elements:
            self.elements[element_id] = {"type": "Button", "text": text, "topic": topic, "data": data, "button_class": button_class, "order": order, "enabled": True}
        else:
            logging.error("Cannot create new UI element with id %s because it already exists" % element_id)
        return NotImplemented

    def add_break(self, element_id, order=99):
        self.elements[element_id] = {"type": "Break", "order": order}

    def get(self, element_id):
        return self.elements[element_id]