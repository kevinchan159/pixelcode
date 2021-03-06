import pixelcode.plugin.utils as utils
from pixelcode.plugin.components.component_factory import ComponentFactory

def add_navbar_items(components):
  """
  Returns (list): components with navbar items added.
  """
  navbar_items = [c.get("navbar-items") for c in components \
                  if c.get("navbar-items")]
  if navbar_items:
    if len(navbar_items) > 1:
      raise Exception("Interpreter_h: More than one navbar is present.")
    navbar_items = navbar_items[0] # only one nav bar per screen
    components.extend(navbar_items['left-buttons'])
    components.extend(navbar_items['right-buttons'])
    if navbar_items.get('title') is not None:
      components.append(navbar_items['title'])
      if navbar_items['title'].get('components') is not None:
        components.extend(navbar_items['title']['components'])
  return components

def add_sliderview_items(components):
  """
  Returns (list): components with slider view items added.
  """
  slider_view = [c for c in components if c["type"] == "SliderView"]
  if not slider_view:
    return components
  elif len(slider_view) > 1:
    raise Exception("Interpreter_h: More than one slider view is present.")
  slider_view = slider_view[0]
  components.append(slider_view["content"])
  components.append(slider_view["slider_options"])
  return components

def add_view_items(components):
  """
  Returns (list): components with view items added.
  """
  views = [c for c in components if c["type"] == "UIView"]
  for view in views:
    if view.get("components") is not None:
      for component in view["components"]:
        if component not in components:
          components.append(component)
  return components

def filter_components(components, types):
  """
  Returns (list): components without any components of a type in types
  """
  return [c for c in components if c["type"] not in types]

def init_g_var(comp):
  """
  Returns: swift code to generate/init one component.
  """
  if comp['type'] == 'UICollectionView': # do not init collection views
    return "var {}: UICollectionView!\n".format(comp['id'])
  elif comp['type'] == 'UINavBar': # cannot init navigation bars
    return ""
  else:
    return "var {} = {}()\n".format(comp['id'], comp['type'])

def init_g_vars(components):
  """
  Args:
    components: (dict list) contains info about components

  Returns (str): swift code to generate/init all glob vars of components
  """
  components = list(components) # get copy of components
  # add slider view items
  components = add_sliderview_items(components)

  # filter components to not include certain components
  filter_comps = filter_components(components, {'SliderView'})

  return "".join([init_g_var(c) for c in filter_comps])

def declare_g_vars(components):
  """
  Returns (str): swift code to declare global variables
  """
  components = list(components) # get copy of comps
  # add navbar items
  components = add_navbar_items(components)
  # add slider view items
  components = add_sliderview_items(components)
  # add view items
  components = add_view_items(components)
  # filter components to not include certain components
  ignore_types = {'UINavBar', 'UIActionSheet', 'SliderView'}
  filter_comps = filter_components(components, ignore_types)

  # one-liner to concat all variable names
  gvars = ["var {}: {}!\n".format(e['id'], e['type']) for e in filter_comps]
  return "".join(gvars)

def adjust_components(components):
  """
  Returns (list): components with necessary components added/removed.
  """
  components = add_navbar_items(components)
  return components # No components to remove as of now.

def gen_global_colors(global_fills, swift):
  """
  Returns (dict): Updated dictionary of all generated files using global colors
  """
  C = ("import UIKit\n\nextension UIColor {\n\n")
  colors = [utils.create_uicolor(f, rgba=True) for f in global_fills]

  for index, color in enumerate(colors): # generate colors file
    color_name = ("color{}").format(index)
    C += "@nonobjc static let {}: UIColor = {}\n".format(color_name, color)
  for (filename, code) in swift.items(): # replace colors in files
    for index, color in enumerate(colors):
      code = code.replace(color, ("UIColor.color{}").format(index))
    swift[filename] = code

  swift["UIColorExtension"] = C + "}\n"
  return swift

def gen_cell_header(type_, cell):
  """
  Args:
    type_ (str): type of the parent (table/collection)view
    cell (dict): info of cell being generated

  Returns (str): swift code to generate the header of a cell
  """
  class_ = utils.uppercase(cell["id"])
  C = ("import UIKit\nimport SnapKit\n\nclass {}: UITableViewCell "
       "{{\n\n{}"
       "\noverride init(style: UITableViewCellStyle, reuseIdentifier: "
       "String?) {{\n"
       "super.init(style: style, reuseIdentifier: reuseIdentifier)\n"
      ).format(class_, init_g_vars(cell.get('components')))

  if type_ == "UICollectionView":
    C = C.replace('style: UITableViewCellStyle, reuseIdentifier: String?',
                  'frame: CGRect')
    C = C.replace('style: style, reuseIdentifier: reuseIdentifier',
                  'frame: frame')
    C = C.replace('Table', 'Collection')

  return C

def gen_header_header(type_, header): # TODO: Rename this function.
  """
  Args:
    type_ (str): type of the parent (table/collection)view
    header: (dict) info of header being generated

  Returns (str): swift code for generating the header of a header
  """
  class_ = utils.uppercase(header["id"])
  C = ("import UIKit\nimport SnapKit\n\nclass {}: "
       "UITableViewHeaderFooterView {{\n\n{}"
       "\noverride init(reuseIdentifier: String?) {{\n"
       "super.init(reuseIdentifier: reuseIdentifier)\n"
      ).format(class_, init_g_vars(header.get('components')))

  if type_ == "UICollectionView":
    C = C.replace('reuseIdentifier: String?', 'frame: CGRect')
    C = C.replace('reuseIdentifier: reuseIdentifier', 'frame: frame')
    C = C.replace('UITableViewHeaderFooterView', 'UICollectionReusableView')

  return C

def gen_viewcontroller_header(view_controller, info, declare_vars):
  """
  Args:
    view_controller (str): name of viewcontroller
    declare_vars (bool): whether or not to declare global variables.

  Returns (str): swift code of the view controller header
  """
  header = ("import UIKit\nimport SnapKit\n\n"
            "class {}: UIViewController {{\n\n"
           ).format(view_controller)
  header += declare_g_vars(info["components"]) if declare_vars else ""
  header += "\noverride func viewDidLoad() {\nsuper.viewDidLoad()\n"
  info["components"] = adjust_components(info["components"])
  return header

def move_collection_view(swift, info):
  """
  Returns (str):
    Returns swift code with UICollectionView setup code moved to current file's
    init function.
  """
  beg = swift.find('layout.')
  mid = swift.find('addSubview', beg)
  end = swift.find('\n', mid)
  cv = ("let layout = UICollectionViewFlowLayout()\n"
        "{} = {}(frame: .zero, collectionViewLayout: layout)\n"
        "{}\n"
       ).format(info['id'], 'UICollectionView', swift[beg:end])
  swift = swift[:beg] + swift[end:]

  if 'reuseIdentifier)\n' in swift:
    swift = utils.ins_after_key(swift, 'reuseIdentifier)\n', cv)
  elif 'frame)\n' in swift:
    swift = utils.ins_after_key(swift, 'frame)\n', cv)

  return swift

def move_action_sheet(swift):
  """
  Returns (str):
    Returns swift code with UIActionSheet setup code moved to current file's
    viewDidAppear function.
  """
  beg = swift.find('let alertController')
  end = swift.find('completion: nil)\n', beg) + 17
  swift += ("\noverride func viewDidAppear(_ animated: Bool) {{\n"
            "{}\n}}\n").format(swift[beg:end])
  swift = swift[:beg] + swift[end:]
  return swift

def subclass_tc(swift, tc_elem):
  """
  Returns (str): adds necessary (table/collection)view parent classes to swift
  """
  ext = ", UITableViewDelegate, UITableViewDataSource"
  if tc_elem['type'] == 'UICollectionView':
    ext = ext.replace('Table', 'Collection')
    ext += ", UICollectionViewDelegateFlowLayout"

  if ext in swift: # parent classes are already added
    return swift

  if ": UIViewController" in swift:
    swift = utils.ins_after_key(swift, ": UIViewController", ext)
  elif ": UITableViewCell" in swift:
    swift = utils.ins_after_key(swift, ": UITableViewCell", ext)
  elif ": UITableViewHeaderFooterView" in swift:
    swift = utils.ins_after_key(swift, ": UITableViewHeaderFooterView", ext)
  elif ": UICollectionReusableView" in swift:
    swift = utils.ins_after_key(swift, ": UICollectionReusableView", ext)
  elif ": UICollectionViewCell" in swift:
    swift = utils.ins_after_key(swift, ": UICollectionViewCell", ext)
  else:
    swift = ""

  return swift

def concat_dicts(d1, d2):
  """
  Args:
    d1, d2 (dict): dictionary whose key and values are both strings

  Returns (dict):
    Concats all (key, value) pairs from d2 to d1. If d2 has a key that d1 does
    not have, the key is added. Otherwise, d2[key] is concatenated onto d1[key].
  """
  for key, value in d2.items():
    if d1.get(key) is None:
      d1[key] = value
    else:
      d1[key] += value
  return d1

def add_methods(methods):
  """
  Returns (str): code of all methods to be added outside of file's init function
  """
  C = ""
  for key, value in methods.items():
    if key == "viewDidAppear":
      C += ("\noverride func viewDidAppear(_ animated: Bool) {{\n"
            "{}\n}}\n\n").format(value)
    elif key == "layoutSubviews":
      C += ("override func layoutSubviews() {{\nsuper.layoutSubviews()\n"
            "{}\n}}\n\n").format(value)
    elif key == "viewDidLayoutSubviews":
      C += ("override func viewDidLayoutSubviews() {{\n"
            "{}\n}}\n\n").format(value)
    elif key in {"tc_methods", "slider_content_methods"}:
      C += value
    else:
      raise Exception("Interpreter_h: Unexpected key in add_methods: " + key)
  return C

def gen_tabbar_file(interpreter, comp):
  """
  Returns (None): Generates tabbar file in interpreter's swift dictionary.
  """
  comp["active_vc"] = interpreter.file_name # Name of active view controller
  cf = ComponentFactory(comp, interpreter.env)
  # Generate tabbar viewcontroller file
  info = interpreter.info
  vc_name = utils.uppercase(comp["id"]) + "ViewController"
  C = gen_viewcontroller_header(vc_name, info, False)
  C = C.replace(': UIViewController', ': UITabBarController')
  C += ("{}}}\n\n").format(cf.swift) + add_methods(cf.methods) + "}\n"

  # Make adjustments if screen contains a navigation bar
  navbar_exists = False
  for component in interpreter.info["components"]:
    if component["type"] == "UINavBar":
      navbar_exists = True
      break
  if navbar_exists:
    nav_controller = ("UINavigationController(rootViewController: {}())"
                     ).format(comp["active_vc"])
    C = C.replace(comp["active_vc"] + "()", nav_controller)

  interpreter.swift[vc_name] = C

def gen_slider_view_pieces(interpreter, comp):
  """
  Returns (None): Generates slider view pieces in interpreter's swift dict.
  """
  # Generate custom SliderOptions class
  slider_opts_id = utils.uppercase(comp["slider_options"]["id"])
  file_name = interpreter.file_name
  interpreter.swift[slider_opts_id] = gen_slider_options(comp, file_name)
  # Generate Content CollectionView
  # Correct Content CollectionView size with respect to artboard
  globals_w = interpreter.globals["width"]
  globals_h = interpreter.globals["height"]
  comp["content"]["width"] = comp["content"]["rwidth"] / globals_w
  comp["content"]["height"] = comp["content"]["rheight"] / globals_h
  content_cf = ComponentFactory(comp["content"], interpreter.env)
  comp["content_swift"] = content_cf.swift
  comp["content_methods"] = content_cf.methods["tc_methods"]
  interpreter.swift[file_name] = subclass_tc(interpreter.swift[file_name],
                                             comp["content"])
  # Generate SliderView CollectionViewCell class
  in_view = interpreter.env["in_view"] # in_view may change while generating
  interpreter.gen_table_collection_view_files(comp["content"])
  interpreter.env["in_view"] = in_view
  interpreter.file_name = file_name

def gen_inset_label():
  """
  Returns (str): swift code of our custom UILabel
  """
  return ("import UIKit\n\n"
          "class InsetLabel: UILabel {\n"
          "let topInset = CGFloat(-10)\n"
          "let bottomInset = CGFloat(-10)\n"
          "let leftInset = CGFloat(0)\n"
          "let rightInset = CGFloat(0)\n\n"
          "override func drawText(in rect: CGRect) {\n"
          "let insets: UIEdgeInsets = UIEdgeInsets(top: topInset, left: "
          "leftInset, bottom: bottomInset, right: rightInset)\n"
          "super.drawText(in: UIEdgeInsetsInsetRect(rect, insets))\n"
          "}\n\n"
          "override public var intrinsicContentSize: CGSize {\n"
          "var intrinsicSuperViewContentSize = super.intrinsicContentSize\n"
          "intrinsicSuperViewContentSize.height += topInset + bottomInset\n"
          "intrinsicSuperViewContentSize.width += leftInset + rightInset\n"
          "return intrinsicSuperViewContentSize\n"
          "}\n"
          "}\n")

def get_navbar_item_ids(info):
  """
  Returns (list): ids of all components inside the given navbar.
  """
  items = info["navbar-items"]
  navbar_item_ids = []
  navbar_item_ids.extend([i["id"] for i in items["left-buttons"]])
  navbar_item_ids.extend([i["id"] for i in items["right-buttons"]])
  if items.get("title") is not None:
    title = items["title"]
    navbar_item_ids.append(title["id"])
    navbar_item_ids.extend(c["id"] for c in title["components"])
  return navbar_item_ids

def gen_slider_options(info, file_name):
  """
  Args:
    info (dict): info on SliderView component

  Returns (str): Custom SliderOptions and SliderOptionCell swift classes.
  """
  slider_options = info["slider_options"]
  options = slider_options["options"]
  first_option = options[0]
  max_size = max_width = max_height = 0

  if first_option.get("text") is not None:
    for option in options:
      size = option["text"]["rwidth"] * option["text"]["rheight"]
      if size > max_size:
        max_size = size
        max_width = option["text"]["width"]
        max_height = option["text"]["height"]
    font = first_option["text"]["font-family"]
    size = first_option["text"]["font-size"]
    cell_gvar = ("let label: UILabel = {{\nlet lab = InsetLabel()\nlab.textAlig"
                 "nment = .center\nlab.numberOfLines = 0\nlab.lineBreakMode = "
                 ".byWordWrapping\nlab.font = {}\nreturn lab\n}}()\n\n"
                ).format(utils.create_font(font, size))
    set_prop = "cell.label.text = names[indexPath.item]\n"
    subview = "label"
  else: # option["img"] is not None
    for option in options:
      size = option["img"]["rwidth"] * option["img"]["rheight"]
      if size > max_size:
        max_size = size
        max_width = option["img"]["width"]
        max_height = option["img"]["height"]
    cell_gvar = "let imageView = UIImageView()\n"
    set_prop = "cell.imageView.image = UIImage(named: names[indexPath.item])\n"
    subview = "imageView"

  if slider_options["rect"].get("fill") is not None:
    cv_fill = utils.create_uicolor(slider_options["rect"]["fill"])
  else:
    cv_fill = ".clear"

  if first_option["rect"].get("fill") is not None:
    cell_fill = ("cell.backGroundColor = {}\n"
                ).format(utils.create_uicolor(first_option["rect"]["fill"]))
  else:
    cell_fill = ""

  selected_index = slider_options["selected_index"]
  selected_option = options[selected_index]
  slider_fill = utils.create_uicolor(selected_option["rect"]["filter"]["fill"])
  constraint = ("{}.snp.updateConstraints{{ make in\n"
                "make.size.equalTo(CGSize(width: frame.width*{}, height: frame"
                ".height*{}))\n"
                "make.center.equalToSuperview()\n}}\n"
               ).format(subview, max_width, max_height)

  bar_width = selected_option["width"]
  bar_height = abs(float(selected_option["rect"]["filter"]["dy"]))
  setup_bar = ("func setupSliderBar() {{\n"
               "sliderBar.backgroundColor = {}\n"
               "addSubview(sliderBar)\n"
               "sliderBarLeftConstraint = sliderBar.leftAnchor.constraint"
               "(equalTo: self.leftAnchor)\n"
               "sliderBarLeftConstraint.isActive = true\n}}\n\n"
              ).format(slider_fill)

  layout_subviews = ("override func layoutSubviews() {{\n"
                     "collectionView.snp.updateConstraints{{ make in\nmake.size"
                     ".equalToSuperview()\nmake.center.equalToSuperview()\n}}\n"
                     "sliderBar.snp.updateConstraints{{ make in\n"
                     "make.size.equalTo(CGSize(width: frame.width*{}, height: "
                     "{}))\nmake.bottom.equalToSuperview()\n}}\n}}\n\n"
                    ).format(bar_width, bar_height)

  slider_opts_name = utils.uppercase(slider_options["id"])
  slider_opts = ("import UIKit\nimport SnapKit\n\n"
                 "class {0}: UIView, UICollectionViewDataSource, "
                 "UICollectionViewDelegate, UICollectionViewDelegateFlowLayout "
                 "{{\n\nlazy var collectionView: UICollectionView = {{\n"
                 "let layout = UICollectionViewFlowLayout()\n"
                 "let cv = UICollectionView(frame: .zero, collectionViewLayout:"
                 " layout)\ncv.backgroundColor = {1}\n"
                 "cv.dataSource = self\ncv.delegate = self\nreturn cv\n}}()\n"
                 "var names: [String]!\n"
                 "let sliderBar = UIView()\nvar sliderBarLeftConstraint: "
                 "NSLayoutConstraint!\nvar controller: {2}!\n\n"
                 "init(frame: CGRect, names: [String], controller: {2}) {{\n"
                 "super.init(frame: frame)\nself.names = names\n"
                 "self.controller = controller\n"
                 "collectionView.register(SliderOptionCell.self, forCellWith"
                 'ReuseIdentifier: "sliderOptionCellId")\n'
                 "addSubview(collectionView)\n"
                 "let selectedIndexPath = IndexPath(item: {3}, section: 0)\n"
                 "collectionView.selectItem(at: selectedIndexPath, animated: "
                 "false, scrollPosition: [])\nsetupSliderBar()\n"
                 "layoutSubviews()\n}}\n\n{4}"
                ).format(slider_opts_name, cv_fill, file_name, selected_index,
                         setup_bar)
  cv_methods = ("func collectionView(_ collectionView: UICollectionView, "
                "numberOfItemsInSection section: Int) -> Int "
                "{{\nreturn names.count\n}}\n\n"
                "func collectionView(_ collectionView: UICollectionView, cell"
                "ForItemAt indexPath: IndexPath) -> UICollectionViewCell {{\n"
                "let cell = collectionView.dequeueReusableCell(withReuseIdentif"
                'ier: "sliderOptionCellId", for: indexPath) as! '
                "SliderOptionCell\n{}{}\nreturn cell\n}}\n\n"
                "func collectionView(_ collectionView: UICollectionView, layout"
                " collectionViewLayout: UICollectionViewLayout, sizeForItemAt"
                " indexPath: IndexPath) -> CGSize {{\n"
                "return CGSize(width: frame.width/CGFloat(names.count), height:"
                " frame.height)\n}}\nfunc "
                "collectionView(_ collectionView: UICollectionView, layout "
                "collectionViewLayout: UICollectionViewLayout, minimumInteritem"
                "SpacingForSectionAt section: Int) -> CGFloat {{\nreturn 0\n}}"
                "\n\n"
                "func collectionView(_ collectionView: UICollectionView, did"
                "SelectItemAt indexPath: IndexPath) {{\ncontroller."
                "scrollToIndex(index: indexPath.item)\n}}\n\n{}\n}}\n\n"
               ).format(set_prop, cell_fill, utils.req_init())
  option_cell = ("class SliderOptionCell: UICollectionViewCell {{\n\n{}"
                 "override init(frame: CGRect) {{\nsuper.init(frame: frame)\n"
                 "layoutSubviews()\n}}\n\n"
                 "override func layoutSubviews() {{\nsuper.layoutSubviews()\n"
                 "addSubview({})\n{}\n}}\n\n{}\n}}\n"
                ).format(cell_gvar, subview, constraint, utils.req_init())
  return slider_opts + layout_subviews + cv_methods + option_cell
