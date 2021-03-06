from . import *

class SliderView(BaseLayer):
  """
  Class representing an SliderView layer in Sketch
  """
  def parse_elem(self, elem):
    slider_options = None
    content = None
    rect = None

    for child in elem["children"]:
      if child["type"] == "SliderOptions":
        slider_options = child
      elif child["type"] == "SliderContent":
        content = child
      elif utils.word_in_str("bound", child["id"]):
        rect = child

    if slider_options is None:
      raise Exception("SliderView: No options in SliderView: " + elem["id"])
    elif content is None:
      raise Exception("SliderView: No content in SliderView: " + elem["id"])

    slider_options["vertical"] = elem["vertical"]
    slider_options["horizontal"] = elem["horizontal"]

    content["id"] = elem["id"] + "CollectionView"
    content["type"] = "UICollectionView"
    cell_name = utils.uppercase(content["id"]) + "Cell"
    cell = {"cell_name": cell_name,
            "components": content["components"],
            "height": 1.0,
            "id": utils.lowercase(cell_name),
            "rect": content.get("rect"),
            "rheight": content["rheight"],
            "rwidth": content["rwidth"],
            "type": "Cell",
            "width": 1.0}
    section = {"cells": [cell],
               "custom_cells": {cell_name: cell},
               "height": 1.0,
               "rect": content.get("rect"),
               "separator": [0],
               "table_separate": False,
               "type": "Section",
               "width": 1.0}
    content.update({"custom_headers": {},
                    "sections": [section],
                    "separator": [0]})
    del content["components"]

    elem["content"] = content
    elem["rect"] = rect
    elem["slider_options"] = slider_options
    return super().parse_elem(elem)
