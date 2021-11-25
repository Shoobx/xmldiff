from copy import deepcopy
from csv import reader
from json import loads
from lxml import etree
from xmldiff import actions


class Patcher(object):

    def patch(self, actions, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        # Copy the tree so we don't modify the original
        result = deepcopy(tree)

        for action in actions:
            self.handle_action(action, result, namespaces)

        return result

    def handle_action(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        action_type = type(action)
        method = getattr(self, '_handle_' + action_type.__name__)
        method(action, tree, namespaces)

    def _handle_DeleteNode(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        node = tree.xpath(action.node, namespaces=namespaces)[0]
        node.getparent().remove(node)

    def _handle_InsertNode(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        target = tree.xpath(action.target, namespaces=namespaces)[0]

        node = target.makeelement(action.tag)
        target.insert(action.position, node)

    def _handle_RenameNode(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        tree.xpath(action.node, namespaces=namespaces)[0].tag = action.tag

    def _handle_MoveNode(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        node = tree.xpath(action.node, namespaces=namespaces)[0]
        node.getparent().remove(node)
        target = tree.xpath(action.target, namespaces=namespaces)[0]
        target.insert(action.position, node)

    def _handle_UpdateTextIn(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        tree.xpath(action.node, namespaces=namespaces)[0].text = action.text

    def _handle_UpdateTextAfter(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        tree.xpath(action.node, namespaces=namespaces)[0].tail = action.text

    def _handle_UpdateAttrib(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        node = tree.xpath(action.node, namespaces=namespaces)[0]
        # This should not be used to insert new attributes.
        assert action.name in node.attrib
        node.attrib[action.name] = action.value

    def _handle_DeleteAttrib(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        del tree.xpath(action.node, namespaces=namespaces)[
            0].attrib[action.name]

    def _handle_InsertAttrib(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        node = tree.xpath(action.node, namespaces=namespaces)[0]
        # This should not be used to update existing attributes.
        assert action.name not in node.attrib
        node.attrib[action.name] = action.value

    def _handle_RenameAttrib(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        node = tree.xpath(action.node, namespaces=namespaces)[0]
        assert action.oldname in node.attrib
        assert action.newname not in node.attrib
        node.attrib[action.newname] = node.attrib[action.oldname]
        del node.attrib[action.oldname]

    def _handle_InsertComment(self, action, tree, namespaces={'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}):
        target = tree.xpath(action.target, namespaces=namespaces)[0]
        target.insert(action.position, etree.Comment(action.text))


class DiffParser(object):
    """Makes a text diff into a list of actions"""

    def parse(self, diff):
        incomplete = ''

        for line in diff.splitlines():
            line = incomplete + line

            if line[0] != '[':
                # All actions should start with "["
                raise ValueError("Unknown diff format")
            if line[-1] != ']':
                # This line has been broken into several lines
                incomplete = line
                continue

            # OK, we found an action
            incomplete = ''
            yield self.make_action(line)

        if incomplete:
            raise ValueError("Diff ended unexpectedly")

    def make_action(self, line):
        # Remove brackets
        line = line[1:-1]
        # Split the line on commas (ignoring commas in quoted strings) and
        # strip extraneous spaces. The first is the action, the rest params.
        parts = [x.strip() for x in next(reader([line]))]
        action = parts[0]
        params = parts[1:]
        # Get the method, and return the result of calling it
        method = getattr(self, '_handle_' + action.replace('-', '_'))
        return method(*params)

    def _handle_delete(self, node):
        return actions.DeleteNode(node)

    def _handle_insert(self, target, tag, position):
        return actions.InsertNode(target, tag, int(position))

    def _handle_rename(self, node, tag):
        return actions.RenameNode(node, tag)

    def _handle_move(self, node, target, position):
        return actions.MoveNode(node, target, int(position))

    def _handle_update_text(self, node, text):
        return actions.UpdateTextIn(node, loads(text))

    def _handle_update_text_after(self, node, text):
        return actions.UpdateTextAfter(node, loads(text))

    def _handle_update_attribute(self, node, name, value):
        return actions.UpdateAttrib(node, name, loads(value))

    def _handle_delete_attribute(self, node, name):
        return actions.DeleteAttrib(node, name)

    def _handle_insert_attribute(self, node, name, value):
        return actions.InsertAttrib(node, name, loads(value))

    def _handle_rename_attribute(self, node, oldname, newname):
        return actions.RenameAttrib(node, oldname, newname)

    def _handle_insert_comment(self, target, position, text):
        return actions.InsertComment(target, int(position), loads(text))
