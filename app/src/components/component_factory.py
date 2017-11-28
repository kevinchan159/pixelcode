import utils
from . import *

class ComponentFactory(object):
  """
  Class used to generate components.
    swift (str): swift code to generate a component
    tv_methods (str): tableview methods for generating a tableview
  """
  def __init__(self, type_, info, in_v, bgc=None):
    """
    Args:
      bgc (tuple): background color of screen
      info (dict): info on component
      in_v (bool): is whether generating from within a custom view
    """
    self.tv_methods = ""
    self.swift = self.generate_component(type_, info, bgc=bgc, in_v=in_v)

  def generate_component(self, type_, info, bgc=None, in_v=False):
    """
    Returns: (str) The swift code to generate component
    """
    id_ = info.get('id')
    rect = info.get('rect')

    C = ""
    if not in_v:
      C += "{} = {}()\n".format(id_, type_)

    C += '{}.translatesAutoresizingMaskIntoConstraints = false\n'.format(id_)

    if rect is not None:
      C += utils.setup_rect(id_, rect, in_v)

    component = utils.create_component(type_, id_, info, {"in_view": in_v})
    C += component.swift

    if type_ == 'UITableView':
      self.tv_methods = component.tv_methods
    elif type_ == 'UILabel':
      C += utils.set_bg(id_, bgc, in_v=in_v)

    view = 'view' if not in_v else None
    C += utils.add_subview(view, id_)
    C += self.gen_constraints(info, in_v=in_v)
    return C

  def gen_constraints(self, info, in_v=False):
    """
    Returns: (str) swift code to set all constraints using SnapKit.
    """
    keys = ['id', 'height', 'width', 'horizontal', 'vertical']
    id_, height, width, hor, vert = utils.get_vals(keys, info)

    keys = ['id', 'direction', 'distance']
    hor_id, hor_dir, hor_dist = utils.get_vals(keys, hor)
    vert_id, vert_dir, vert_dist = utils.get_vals(keys, vert)

    C = ("{}.snp.updateConstraints {{ make in\n"
         "make.size.equalTo(CGSize(width: frame.width*{}, height: "
         "frame.height*{}))\n"
        ).format(id_, width, height)

    if hor_id:
      opp_dir = self.get_opp_dir(hor_dir)
      C += ('make.{}.equalTo({}.snp.{}).offset(frame.width*{})\n'
           ).format(hor_dir, hor_id, opp_dir, hor_dist)
    else:
      C += ('make.left.equalToSuperview().offset(frame.width*{})\n'
           ).format(hor_dist)

    if vert_id:
      opp_dir = self.get_opp_dir(vert_dir)
      C += ('make.{}.equalTo({}.snp.{}).offset(frame.height*{})\n'
           ).format(vert_dir, vert_id, opp_dir, vert_dist)
    else:
      C += ('make.top.equalToSuperview().offset(frame.height*{})\n'
           ).format(vert_dist)
    C += "}\n\n"

    if not in_v:
      C = C.replace("frame", "view.frame")
    return C

  def get_opp_dir(self, d):
    """
    Returns: direction opposite to [d]
    """
    return {
        "top": "bottom",
        "bottom": "top",
        "left": "right",
        "right": "left"
    }[d]