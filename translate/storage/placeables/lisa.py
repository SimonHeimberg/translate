#
# Copyright 2008-2009,2011 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from lxml import etree

from translate.misc.xml_helpers import normalize_xml_space
from translate.storage.placeables import StringElem, base, xliff
from translate.storage.xml_extract import misc

__all__ = ("xml_to_strelem", "strelem_to_xml")
# Use the above functions as entry points into this module. The rest are
# used by these functions.


def make_empty_replacement_placeable(klass, node, xml_space="preserve"):
    try:
        return klass(
            id=node.attrib["id"],
            rid=node.attrib.get("rid", None),
            xid=node.attrib.get("xid", None),
            xml_attrib=node.attrib,
        )
    except KeyError:
        pass
    return klass()


def make_g_placeable(klass, node, xml_space="default"):
    return klass(
        id=node.attrib["id"],
        sub=xml_to_strelem(node, xml_space).sub,
        xml_attrib=node.attrib,
    )


def not_yet_implemented(klass, node, xml_space="preserve"):
    raise NotImplementedError


def make_unknown(klass, node, xml_space="preserve"):
    assert klass is xliff.UnknownXML

    sub = xml_to_strelem(node, xml_space).sub
    id = node.get("id", None)
    rid = node.get("rid", None)
    xid = node.get("xid", None)

    return klass(sub=sub, id=id, rid=rid, xid=xid, xml_node=node)


_class_dictionary = {
    #'bpt': (xliff.Bpt, not_yet_implemented),
    "bx": (xliff.Bx, make_empty_replacement_placeable),
    #'ept': (xliff.Ept, not_yet_implemented),
    "ex": (xliff.Ex, make_empty_replacement_placeable),
    "g": (xliff.G, make_g_placeable),
    #'it': (xliff.It, not_yet_implemented),
    #'ph': (xliff.Ph, not_yet_implemented),
    #'sub': (xliff.Sub, not_yet_implemented),
    "x": (xliff.X, make_empty_replacement_placeable),
}


def make_placeable(node, xml_space):
    _namespace, tag = misc.parse_tag(node.tag)
    if tag in _class_dictionary:
        klass, maker = _class_dictionary[tag]
    else:
        klass, maker = xliff.UnknownXML, make_unknown
    return maker(klass, node, xml_space)


def as_unicode(string):
    if isinstance(string, str):
        return string
    elif isinstance(string, StringElem):
        return str(string)
    else:
        return string.decode("utf-8")


def xml_to_strelem(dom_node, xml_space="preserve"):
    if dom_node is None:
        return StringElem()
    if isinstance(dom_node, str):
        parser = etree.XMLParser(resolve_entities=False)
        dom_node = etree.fromstring(dom_node, parser)
    normalize_xml_space(dom_node, xml_space, remove_start=True)
    result = StringElem()
    sub = result.sub  # just an optimisation
    for child_dom_node in dom_node:
        if child_dom_node.tag is etree.Comment:
            continue
        sub.append(make_placeable(child_dom_node, xml_space))
        if child_dom_node.tail:
            sub.append(StringElem(str(child_dom_node.tail)))

    # This is just a strange way of inserting the first text and avoiding a
    # call to .prune() which is very expensive. We assume the tree is optimal.
    node_text = dom_node.text
    if sub and node_text:
        sub.insert(0, StringElem(str(node_text)))
    elif node_text:
        sub.append(str(node_text))
    return result


# ==========================================================


def placeable_as_dom_node(placeable, tagname):
    dom_node = etree.Element(tagname)
    if placeable.id is not None:
        dom_node.attrib["id"] = placeable.id
    if placeable.xid is not None:
        dom_node.attrib["xid"] = placeable.xid
    if placeable.rid is not None:
        dom_node.attrib["rid"] = placeable.rid

    if hasattr(placeable, "xml_attrib"):
        for attrib, value in placeable.xml_attrib.items():
            dom_node.set(attrib, value)

    return dom_node


def unknown_placeable_as_dom_node(placeable):
    assert type(placeable) is xliff.UnknownXML

    from copy import copy

    node = copy(placeable.xml_node)
    for i in range(len(node)):
        del node[0]
    node.tail = None
    node.text = None

    return node


_placeable_dictionary = {
    xliff.Bpt: lambda placeable: placeable_as_dom_node(placeable, "bpt"),
    xliff.Bx: lambda placeable: placeable_as_dom_node(placeable, "bx"),
    xliff.Ept: lambda placeable: placeable_as_dom_node(placeable, "ept"),
    xliff.Ex: lambda placeable: placeable_as_dom_node(placeable, "ex"),
    xliff.G: lambda placeable: placeable_as_dom_node(placeable, "g"),
    xliff.It: lambda placeable: placeable_as_dom_node(placeable, "it"),
    xliff.Ph: lambda placeable: placeable_as_dom_node(placeable, "ph"),
    xliff.Sub: lambda placeable: placeable_as_dom_node(placeable, "sub"),
    xliff.X: lambda placeable: placeable_as_dom_node(placeable, "x"),
    xliff.UnknownXML: unknown_placeable_as_dom_node,
    base.Bpt: lambda placeable: placeable_as_dom_node(placeable, "bpt"),
    base.Bx: lambda placeable: placeable_as_dom_node(placeable, "bx"),
    base.Ept: lambda placeable: placeable_as_dom_node(placeable, "ept"),
    base.Ex: lambda placeable: placeable_as_dom_node(placeable, "ex"),
    base.G: lambda placeable: placeable_as_dom_node(placeable, "g"),
    base.It: lambda placeable: placeable_as_dom_node(placeable, "it"),
    base.Ph: lambda placeable: placeable_as_dom_node(placeable, "ph"),
    base.Sub: lambda placeable: placeable_as_dom_node(placeable, "sub"),
    base.X: lambda placeable: placeable_as_dom_node(placeable, "x"),
}


def xml_append_string(node, string):
    if not len(node):
        if not node.text:
            node.text = str(string)
        else:
            node.text += str(string)
    else:
        lastchild = node.getchildren()[-1]
        if lastchild.tail is None:
            lastchild.tail = ""
        lastchild.tail += str(string)
    return node


def strelem_to_xml(parent_node, elem):
    if isinstance(elem, str):
        return xml_append_string(parent_node, elem)
    if not isinstance(elem, StringElem):
        return parent_node

    if type(elem) is StringElem and elem.isleaf():
        return xml_append_string(parent_node, elem)

    if elem.__class__ in _placeable_dictionary:
        node = _placeable_dictionary[elem.__class__](elem)
        parent_node.append(node)
    else:
        node = parent_node

    for sub in elem.sub:
        strelem_to_xml(node, sub)

    return parent_node


def parse_xliff(pstr):
    parser = etree.XMLParser(resolve_entities=False)
    return xml_to_strelem(etree.fromstring("<source>%s</source>" % (pstr), parser))


xliff.parsers = [parse_xliff]
