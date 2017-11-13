from layers.rect import Rect
from layers.text import Text
from . import *

class Button(BaseLayer):
  """
  Class representing a Button in Sketch
  """
  def parse_elem(self, elem):
    rect = None
    text = None
    for child in elem["children"]:
      if child.name == "rect":
        rect = child
      elif child.name == "text":
        text = child

    if text is None:
      raise Exception("Text cannot be empty in a button.")

    elem["rect"] = Rect(rect)
    elem["text"] = Text(text)
    return super(Button, self).parse_elem(elem)
