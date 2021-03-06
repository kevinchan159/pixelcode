import math
from .rect import Rect
from .text import Text
from . import *

class TableCollectionView(BaseLayer):
  """
  Class representing a TableView layer in Sketch
  """
  def parse_elem(self, elem):
    rect = None
    sections = []

    for child in elem["children"]:
      if child["type"] == "Section":
        sections.append(child)
      elif utils.word_in_str("bound", child["id"]):
        if rect:
          raise Exception("TableCollectionView: Only one bound allowed")
        else:
          rect = child

    if not sections:
      raise Exception("TableCollectionView: No sections in " + elem["id"])

    # Calculate cell spacing for all sections
    sections = sorted(sections, key=lambda s: s['y']) # sort by y
    type_ = elem["type"]
    sections = [self.calculate_separator(sect, type_) for sect in sections]

    # Calculate spacing between sections
    separator = []
    if len(sections) >= 2:
      section_sep = sections[1]['y'] - sections[0]['y'] - sections[0]['rheight']
      separator.append(section_sep)

    # Get all the custom headers
    custom_headers = {}
    for section in sections:
      if section.get("header") is not None:
        header = section["header"]
        index = utils.index_of(header["id"], "header")
        header_name = utils.uppercase(header["id"][:index + 6])
        header["header_name"] = header_name
        if custom_headers.get(header_name) is None:
          custom_headers[header_name] = header

    # Check scroll direction indicator for UICollectionView
    scroll_dir = None
    if type_ == "UICollectionView" and ":" in elem["id"]:
      index = elem["id"].find(":")
      scroll_indicator = elem["id"][index:]
      if utils.word_in_str("horizontal", scroll_indicator):
        scroll_dir = "horizontal"
      elif utils.word_in_str("vertical", scroll_indicator):
        scroll_dir = "vertical"
      else:
        raise Exception("TableCollectionView: ':' found in name.")
      elem["id"] = elem["id"][:index]


    elem["custom_headers"] = custom_headers
    elem["rect"] = rect
    elem["scroll_dir"] = scroll_dir
    elem["sections"] = sections
    elem["separator"] = separator
    return super().parse_elem(elem)

  def calculate_separator(self, section, type_):
    """
    Returns (dict): Section dict with "separator" and "table_separate" key added
    """
    cells = section["cells"]
    separator = []
    if len(cells) >= 2:
      if type_ == 'UITableView':
        vert_sep = cells[1]['y'] - cells[0]['y'] - cells[0]['rheight']
        separator = [vert_sep]
      else:
        hor_sep = cells[1]['x'] - cells[0]['x'] - cells[0]['rwidth']
        separator = [hor_sep]
        next_row_cell = None
        for cell in cells:
          if cell['y'] > cells[0]['y']:
            next_row_cell = cell
            break
        if next_row_cell is not None: # more than one row exists
          vert_sep = next_row_cell['y'] - cells[0]['y'] - cells[0]['rheight']
          separator.append(vert_sep)
    section["separator"] = separator
    section["table_separate"] = (type_ == "UITableView" and \
                                 len(separator) > 0 and \
                                 separator[0] > 0)
    return section
