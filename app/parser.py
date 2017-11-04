import json
from bs4 import BeautifulSoup
from layers import *
import utils

class Parser(object):
  """
  Parses a SVG file and outputs a dictionary with necessary attributes
    elements: list of elements in svg
    filepath: path to file
    globals: dictionary with keys
      - width (int)
      - height (int)
      - background_color (tuple)
      - pagename (str)
      - artboard (str)
  """
  def __init__(self, path, artboard):
    """
    Returns: Parser object for parsing the file located at filepath
    """
    self.artboard = artboard
    self.elements = []
    self.json = {}
    self.globals = {}
    self.path = path

  def parse_artboard(self):
    """
    Parses artboard with name [self.artboard]
    """
    self.parse_json()
    self.parse_svg()

  def parse_json(self):
    """
    Initializes self.json
    """
    f = open(self.path + self.artboard + ".json", "r+")
    self.json = json.loads(f.read())

  def parse_svg(self):
    """
    Returns: Parses an SVG and sets instance variables appropriately
    """
    f = open(self.path + self.artboard + ".svg", "r+")
    soup = BeautifulSoup(f, "lxml")
    f.close()

    self.globals = self.parse_globals(soup.svg)
    self.elements = self.parse_elements(
        self.inherit_from(soup.svg.g, soup.svg.g.g)
    )

  def parse_globals(self, svg):
    """
    Returns: dict of globals taken from parsing svg element
    """
    bg_color = svg["style"][:-1].split(" ")[1] # parse hexcode
    height = svg["height"][:-2]
    width = svg["width"][:-2]
    pagename = svg.g["id"]
    artboard = svg.g.g["id"]
    return {"background_color": utils.convert_hex_to_rgb(bg_color),
            "width": int(width),
            "height": int(height),
            "pagename": pagename,
            "artboard": artboard}

  def parse_elements(self, artboard):
    """
    Returns: list of parsed elements
    """
    # grab elements, append attributes, sort by bottom-right coordinate
    elements = []
    for elem in artboard.children:
      if elem != "\n":
        elem = self.inherit_from(artboard, elem)
        elem = self.inherit_from_json(elem)
        elements.append(elem)
    elements.sort(key=lambda e: (int(e["x"]) + int(e["y"]) +
                                 int(e["width"]) + int(e["height"])))

    parsed_elements = []
    for elem in elements:
      vertical = {}
      horizontal = {}

      for check in parsed_elements:
        if vertical == {}:
          check_up = utils.check_spacing(check, elem, "up")
          if check_up[0]:
            vertical = {"direction": "up", "id": check["id"],
                        "distance": check_up[1]}
        if horizontal == {}:
          check_left = utils.check_spacing(check, elem, "left")
          if check_left[0]:
            horizontal = {"direction": "left", "id": check["id"],
                          "distance": check_left[1]}
        if vertical != {} and horizontal != {}:
          break

      if vertical == {}:
        vertical = {"direction": "up", "id": "", "distance": int(elem["y"])}
      if horizontal == {}:
        horizontal = {"direction": "left", "id": "", "distance": int(elem["x"])}

      # convert units to percentages
      elem["width"] = int(elem["width"]) / (1.0 * self.globals["width"])
      elem["height"] = int(elem["height"]) / (1.0 * self.globals["height"])
      elem["x"] = int(elem["x"]) / (1.0 * self.globals["width"])
      elem["y"] = int(elem["y"]) / (1.0 * self.globals["height"])
      vertical["distance"] /= (1.0 * self.globals["height"])
      horizontal["distance"] /= (1.0 * self.globals["width"])

      if elem.name == "rect":
        parsed_elem = Rect(elem, vertical, horizontal)
      elif elem.name == "text":
        elem["contents"] = elem.tspan.contents[0]
        parsed_elem = Text(elem, vertical, horizontal)
      new_elem = parsed_elem.elem
      parsed_elements.insert(0, new_elem)
    return parsed_elements[::-1]

  def inherit_from(self, parent, child):
    """
    Returns: child with attributes from parent not defined in child passed down
    """
    for attr in parent.attrs:
      if attr not in child.attrs:
        child[attr] = parent[attr]
    return child

  def inherit_from_json(self, child):
    """
    Returns: child with attributes from json not defined in child passed down
    """
    for layer in self.json["layers"]:
      if child["id"] == layer["name"]:
        for key in layer.keys():
          if key != "name":
            child[key] = layer[key]
        break
    return child
