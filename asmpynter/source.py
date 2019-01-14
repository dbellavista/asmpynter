
class Instruction(object):

  def __init__(self, string):
    self.string = string

  def __str__(self):
    return self.string

class Source(object):

  def __init__(self):
    self.source = []

  def add_instruction(self, inst):
    self.source.append(inst)

  def clear_instructions(self):
    self.source = []

  def remove_last_istruction(self):
    if len(self.source) > 0:
      return self.source.pop()
    return None

  def instructions_len(self):
    return len(self.source)

  def __str__(self):
    return self._ist_to_source()

  def _ist_to_source(self):
    res = ""
    for i in self.source:
      res = res + "  " + str(i) + "\n"
    return res
