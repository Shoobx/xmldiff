from collections import namedtuple

# The edit script actions used in xmldiff
DeleteNode = namedtuple('DeleteNode', 'node')
InsertNode = namedtuple('InsertNode', 'target tag position')
RenameNode = namedtuple('RenameNode', 'node tag')
MoveNode = namedtuple('MoveNode', 'node target position')

UpdateTextIn = namedtuple('UpdateTextIn', 'node text')
UpdateTextAfter = namedtuple('UpdateTextAfter', 'node text')

UpdateAttrib = namedtuple('UpdateAttrib', 'node name value')
DeleteAttrib = namedtuple('DeleteAttrib', 'node name')
InsertAttrib = namedtuple('InsertAttrib', 'node name value')
RenameAttrib = namedtuple('RenameAttrib', 'node oldname newname')

InsertComment = namedtuple('InsertComment', 'target position text')
