from collections import namedtuple

# The edit script actions used in xmldiff
DeleteNode = namedtuple('DeleteNode', 'node tag')
InsertNode = namedtuple('InsertNode', 'target tag position')
RenameNode = namedtuple('RenameNode', 'node tag node_right tag_left')
MoveNode = namedtuple('MoveNode', 'node target position')

UpdateTextIn = namedtuple('UpdateTextIn', 'node text node_right text_left')
UpdateTextAfter = namedtuple('UpdateTextAfter', 'node text node_right text_left')

UpdateAttrib = namedtuple('UpdateAttrib', 'node name value node_right left_value')
DeleteAttrib = namedtuple('DeleteAttrib', 'node name value')
InsertAttrib = namedtuple('InsertAttrib', 'node name value')
RenameAttrib = namedtuple('RenameAttrib', 'node oldname newname node_right')

InsertComment = namedtuple('InsertComment', 'target position text')
