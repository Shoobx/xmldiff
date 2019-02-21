from copy import deepcopy
from lxml import etree


class Patcher(object):

    def patch(self, actions, tree):
        # Copy the tree so we don't modify the original
        result = deepcopy(tree)

        for action in actions:
            self.handle_action(action, result)

        return result

    def handle_action(self, action, tree):
        action_type = type(action)
        method = getattr(self, '_handle_' + action_type.__name__)
        method(action, tree)

    def _handle_DeleteNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)

    def _handle_InsertNode(self, action, tree):
        target = tree.xpath(action.target)[0]
        node = target.makeelement(action.tag)
        target.insert(action.position, node)

    def _handle_RenameNode(self, action, tree):
        tree.xpath(action.node)[0].tag = action.tag

    def _handle_MoveNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)
        target = tree.xpath(action.target)[0]
        target.insert(action.position, node)

    def _handle_UpdateTextIn(self, action, tree):
        tree.xpath(action.node)[0].text = action.text

    def _handle_UpdateTextAfter(self, action, tree):
        tree.xpath(action.node)[0].tail = action.text

    def _handle_UpdateAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to insert new attributes.
        assert action.name in node.attrib
        node.attrib[action.name] = action.value

    def _handle_DeleteAttrib(self, action, tree):
        del tree.xpath(action.node)[0].attrib[action.name]

    def _handle_InsertAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to update existing attributes.
        assert action.name not in node.attrib
        node.attrib[action.name] = action.value

    def _handle_RenameAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        assert action.oldname in node.attrib
        assert action.newname not in node.attrib
        node.attrib[action.newname] = node.attrib[action.oldname]
        del node.attrib[action.oldname]

    def _handle_InsertComment(self, action, tree):
        target = tree.xpath(action.target)[0]
        target.insert(action.position, etree.Comment(action.text))
