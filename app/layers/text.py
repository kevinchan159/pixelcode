import utils

class Text(object):
  def __init__(self, elem, vertical, horizontal):
    """
    Args:
      elem (dict): represents a text layer from sketch to be parsed.
      vertical (dict): represents the vertical spacing from other objects.
      horizontal (dict): represents the horizontal spacing from other objects.
    """
    self.elem = self.parse_elem(elem, vertical, horizontal)

  def parse_elem(self, elem, vertical, horizontal):
    """
    Args:
      Refer to args in __init__
    """
    center_x = ((elem["x"] + elem["width"]) / 2)
    center_y = ((elem["y"] + elem["height"]) / 2)
    return {
        "type": "UILabel", "id": elem["id"],
        "text": elem["contents"],
        "text-color": utils.convert_hex_to_rgb(elem["fill"]),
        "font-size": elem["font-size"],
        "x": center_x, "y": center_y,
        "width": elem["width"], "height": elem["height"],
        "vertical": vertical, "horizontal": horizontal}
