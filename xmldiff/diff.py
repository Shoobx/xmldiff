from copy import deepcopy
from difflib import SequenceMatcher
from lxml import etree
from math import sqrt
from xmldiff import utils, actions


class Differ:
    def __init__(
        self,
        F=None,
        uniqueattrs=None,
        ratio_mode="fast",
        fast_match=False,
        best_match=False,
        ignored_attrs=[],
    ):
        # The minimum similarity between two nodes to consider them equal
        if F is None:
            F = 0.5
        self.F = F
        # uniqueattrs is a list of attributes or (tag, attribute) pairs
        # that uniquely identifies a node inside a document. Defaults
        # to 'xml:id'.
        if uniqueattrs is None:
            uniqueattrs = ["{http://www.w3.org/XML/1998/namespace}id"]
        self.uniqueattrs = uniqueattrs
        self.fast_match = fast_match
        self.best_match = best_match

        # Avoid recreating this for every node
        self._sequencematcher = SequenceMatcher()
        if ratio_mode == "fast":
            self._sequence_ratio = self._sequencematcher.quick_ratio
        elif ratio_mode == "accurate":
            self._sequence_ratio = self._sequencematcher.ratio
        elif ratio_mode == "faster":
            self._sequence_ratio = self._sequencematcher.real_quick_ratio
        else:
            raise ValueError("Unknown ratio_mode '%s'" % ratio_mode)

        self.ignored_attrs = ignored_attrs

        self.clear()

    def clear(self):
        # Use None for all values, as markings that they aren't done yet.
        self.left = None
        self.right = None
        self._matches = None
        self._l2rmap = None
        self._r2lmap = None
        self._inorder = None
        # Well, except the text cache, it's used by the ratio tests,
        # so we set that to a dict so the tests work.
        self._text_cache = {}

    def set_trees(self, left, right):
        self.clear()

        # Make sure we were passed two lxml elements:
        if isinstance(left, etree._ElementTree):
            left = left.getroot()
        if isinstance(right, etree._ElementTree):
            right = right.getroot()

        if not (etree.iselement(left) and etree.iselement(right)):
            raise TypeError("The 'left' and 'right' parameters must be lxml Elements.")

        # Left gets modified as a part of the diff, deepcopy it first.
        self.left = deepcopy(left)
        self.right = right

    def append_match(self, lnode, rnode, max_match):
        self._matches.append((lnode, rnode, max_match))
        self._l2rmap[id(lnode)] = rnode
        self._r2lmap[id(rnode)] = lnode

    def match(self, left=None, right=None):
        # This is not a generator, because the diff() functions needs
        # _l2rmap and _r2lmap, so if match() was a generator, then
        # diff() would have to first do list(self.match()) without storing
        # the result, and that would be silly.

        # Nothing in this library is actually using the resulting list of
        # matches match() returns, but it may be useful for somebody that
        # actually do not want a diff, but only a list of matches.
        # It also makes testing the match function easier.

        if left is not None or right is not None:
            self.set_trees(left, right)

        if self._matches is not None:
            # We already matched these sequences, use the cache
            return self._matches

        # Initialize the caches:
        self._matches = []
        self._l2rmap = {}
        self._r2lmap = {}
        self._inorder = set()
        self._text_cache = {}

        # Generate the node lists
        lnodes = list(utils.post_order_traverse(self.left))
        rnodes = list(utils.post_order_traverse(self.right))

        # TODO: If the roots do not match, we should create new roots, and
        # have the old roots be children of the new roots, but let's skip
        # that for now, we don't need it. That's strictly a part of the
        # insert phase, but hey, even the paper defining the phases
        # ignores the phases, so...
        # For now, just make sure the roots are matched, we do that by
        # removing them from the lists of nodes, so it can't match, and add
        # them back last.
        lnodes.remove(self.left)
        rnodes.remove(self.right)

        if self.fast_match:
            # First find matches with longest_common_subsequence:
            matches = list(
                utils.longest_common_subsequence(
                    lnodes, rnodes, lambda x, y: self.node_ratio(x, y) >= self.F
                )
            )

            # Add the matches (I prefer this from start to finish):
            for left_match, right_match in matches:
                self.append_match(lnodes[left_match], rnodes[right_match], None)

            # Then remove the nodes (needs to be done backwards):
            for left_match, right_match in reversed(matches):
                lnodes.pop(left_match)
                rnodes.pop(right_match)

        elif self.best_match:
            unmatched_lnodes = []

            # First find all nodes that match perfectly
            for lnode in lnodes:
                max_match = 0
                match_node = None

                for rnode in rnodes:
                    match = self.node_ratio(lnode, rnode)
                    if match == 1.0:
                        self.append_match(lnode, rnode, 1.0)
                        rnodes.remove(rnode)
                        break

                    if match > max_match:
                        match_node = rnode
                        max_match = match
                else:
                    unmatched_lnodes.append((lnode, match_node, max_match))
                    # unmatched_lnodes.append(lnode)

            lnodes = []
            for lnode, rnode, max_match in unmatched_lnodes:
                if max_match >= self.F and rnode in rnodes:
                    self.append_match(lnode, rnode, max_match)
                else:
                    lnodes.append(lnode)

        for lnode in lnodes:
            max_match = 0
            match_node = None

            for rnode in rnodes:
                match = self.node_ratio(lnode, rnode)
                if match > max_match:
                    match_node = rnode
                    max_match = match

                # Try to shortcut for nodes that are not only equal but also
                # in the same place in the tree
                if match == 1.0:
                    # This is a total match, break here
                    break

            if max_match >= self.F:
                self.append_match(lnode, match_node, max_match)

                # We don't want to check nodes that already are matched
                if match_node is not None:
                    rnodes.remove(match_node)

        # Match the roots
        self.append_match(self.left, self.right, 1.0)
        return self._matches

    def node_ratio(self, left, right):
        if left.tag is etree.Comment or right.tag is etree.Comment:
            if left.tag is etree.Comment and right.tag is etree.Comment:
                # comments
                self._sequencematcher.set_seqs(left.text, right.text)
                return self._sequence_ratio()
            # One is a comment the other is not:
            return 0

        for attr in self.uniqueattrs:
            if not isinstance(attr, str):
                # If it's actually a sequence of (tag, attr), the tags must
                # match first.
                tag, attr = attr
                if tag != left.tag or tag != right.tag:
                    continue
            if attr in left.attrib or attr in right.attrib:
                # One of the nodes have a unique attribute, we check only that.
                # If only one node has it, it means they are not the same.
                return int(left.attrib.get(attr) == right.attrib.get(attr))

        match = self.leaf_ratio(left, right)
        child_ratio = self.child_ratio(left, right)

        if child_ratio is not None:
            match = sqrt((match**2 + child_ratio**2) / 2)
        return match

    def node_text(self, node):
        if node in self._text_cache:
            return self._text_cache[node]
        # Get the texts and the tag as a start
        texts = [node.tag] + node.xpath("text()")

        # Then add attributes and values
        for tag, value in sorted(self.node_attribs(node).items()):
            if tag[0] == "{":
                tag = tag.split(
                    "}",
                )[-1]
            texts.append(f"{tag}:{value}")

        # Finally make one string, useful to see how similar two nodes are
        text = " ".join(texts).strip()
        result = utils.cleanup_whitespace(text)
        self._text_cache[node] = result
        return result

    def node_attribs(self, node):
        """Return a dict of attributes to consider for this node."""
        attribs = dict(node.attrib)
        for key in self.ignored_attrs:
            attribs.pop(key, None)
        return attribs

    def leaf_ratio(self, left, right):
        # How similar two nodes are, with no consideration of their children
        # We use a simple ratio here, I tried Levenshtein distances
        # but that took a 100 times longer.
        ltext = self.node_text(left)
        rtext = self.node_text(right)
        self._sequencematcher.set_seqs(ltext, rtext)
        return self._sequence_ratio()

    def child_ratio(self, left, right):
        # How similar the children of two nodes are
        left_children = left.getchildren()
        right_children = right.getchildren()
        if not left_children and not right_children:
            return None

        count = 0
        child_count = max((len(left_children), len(right_children)))
        for lchild in left_children:
            for rchild in right_children:
                if self._l2rmap.get(id(lchild)) is rchild:
                    count += 1
                    right_children.remove(rchild)
                    break

        return count / child_count

    def update_node_tag(self, left, right):
        if left.tag != right.tag:
            left_xpath = utils.getpath(left)
            yield actions.RenameNode(left_xpath, right.tag)
            left.tag = right.tag

    def update_node_attr(self, left, right):
        left_xpath = utils.getpath(left)

        # Update: Look for differences in attributes

        left_keys = set(self.node_attribs(left).keys())
        right_keys = set(self.node_attribs(right).keys())
        new_keys = right_keys.difference(left_keys)
        removed_keys = left_keys.difference(right_keys)
        common_keys = left_keys.intersection(right_keys)

        # We sort the attributes to get a consistent order in the edit script.
        # That's only so we can do testing in a reasonable way...
        for key in sorted(common_keys):
            if left.attrib[key] != right.attrib[key]:
                yield actions.UpdateAttrib(left_xpath, key, right.attrib[key])
                left.attrib[key] = right.attrib[key]

        # Align: Not needed here, we don't care about the order of
        # attributes.

        # Move: Check if any of the new attributes have the same value
        # as the removed attributes. If they do, it's actually
        # a renaming, and a move is one action instead of remove + insert
        newattrmap = {v: k for (k, v) in right.attrib.items() if k in new_keys}
        for lk in sorted(removed_keys):
            value = left.attrib[lk]
            if value in newattrmap:
                rk = newattrmap[value]
                yield actions.RenameAttrib(left_xpath, lk, rk)
                # Remove from list of new attributes
                new_keys.remove(rk)
                # Delete used attribute from map of attributes
                del newattrmap[value]
                # Update left node
                left.attrib[rk] = value
                del left.attrib[lk]

        # Insert: Find new attributes
        for key in sorted(new_keys):
            yield actions.InsertAttrib(left_xpath, key, right.attrib[key])
            left.attrib[key] = right.attrib[key]

        # Delete: remove removed attributes
        for key in sorted(removed_keys):
            if key not in left.attrib:
                # This was already moved
                continue
            yield actions.DeleteAttrib(left_xpath, key)
            del left.attrib[key]

    def update_node_text(self, left, right):
        left_xpath = utils.getpath(left)

        if left.text != right.text:
            yield actions.UpdateTextIn(left_xpath, right.text, left.text)
            left.text = right.text

        if left.tail != right.tail:
            yield actions.UpdateTextAfter(left_xpath, right.tail, left.tail)
            left.tail = right.tail

    def find_pos(self, node):
        parent = node.getparent()
        # The paper here first checks if the child is the first child in
        # order, but I am entirely unable to actually make that happen, and
        # if it does, the "else:" will catch that case anyway, and it also
        # deals with the case of no child being in order.

        # Find the last sibling before the child that is in order
        i = parent.index(node)
        while i >= 1:
            i -= 1
            sibling = parent[i]
            if sibling in self._inorder:
                # That's it
                break
        else:
            # No previous sibling in order.
            return 0

        # Now find the partner of this in the left tree
        sibling_match = self._r2lmap[id(sibling)]
        node_match = self._r2lmap.get(id(node))

        i = 0
        for child in sibling_match.getparent().getchildren():
            if child is node_match:
                # Don't count the node we're looking for.
                continue
            if child in self._inorder or child not in self._l2rmap:
                # Count nodes that are in order, or will be deleted:
                i += 1
            if child is sibling_match:
                # We found the position!
                break
        return i

    def align_children(self, left, right):
        lchildren = [
            c
            for c in left.getchildren()
            if (id(c) in self._l2rmap and self._l2rmap[id(c)].getparent() is right)
        ]
        rchildren = [
            c
            for c in right.getchildren()
            if (id(c) in self._r2lmap and self._r2lmap[id(c)].getparent() is left)
        ]
        if not lchildren or not rchildren:
            # Nothing to align
            return

        lcs = utils.longest_common_subsequence(
            lchildren, rchildren, lambda x, y: self._l2rmap[id(x)] is y
        )

        for x, y in lcs:
            # Mark these as in order
            self._inorder.add(lchildren[x])
            self._inorder.add(rchildren[y])

        # Go over those children that are not in order:
        for lchild in lchildren:
            if lchild in self._inorder:
                # Already aligned
                continue

            rchild = self._l2rmap[id(lchild)]
            right_pos = self.find_pos(rchild)
            rtarget = rchild.getparent()
            ltarget = self._r2lmap[id(rtarget)]
            yield actions.MoveNode(
                utils.getpath(lchild), utils.getpath(ltarget), right_pos
            )
            # Do the actual move:
            left.remove(lchild)
            ltarget.insert(right_pos, lchild)
            # Mark the nodes as in order
            self._inorder.add(lchild)
            self._inorder.add(rchild)

    def diff(self, left=None, right=None):
        # Make sure the matching is done first, diff() needs the l2r/r2l maps.
        if not self._matches:
            self.match(left, right)

        # First, deal with namespaces:
        rnsmap = self.right.nsmap
        lnsmap = self.left.nsmap
        for k, v in rnsmap.items():
            # Make sure it's registered:
            if k is not None and not utils.RESERVED_NS.match(k):
                etree.register_namespace(k, v)
            if k not in lnsmap:
                yield actions.InsertNamespace(k, v)
            elif lnsmap[k] != v:
                raise RuntimeError(
                    "Sorry, we do not support changing the URI of namespaces in xmldiff"
                )

        for k, v in lnsmap.items():
            # Make sure it's registered:
            if k is not None and not utils.RESERVED_NS.match(k):
                etree.register_namespace(k, v)
            if k not in rnsmap:
                yield actions.DeleteNamespace(k)

        # The paper talks about the five phases, and then does four of them
        # in one phase, in a different order that described. This
        # implementation in turn differs in order yet again.
        ltree = self.left.getroottree()

        for rnode in utils.breadth_first_traverse(self.right):
            # (a)
            rparent = rnode.getparent()
            ltarget = self._r2lmap.get(id(rparent))

            # (b) Insert
            if id(rnode) not in self._r2lmap:
                # (i)
                pos = self.find_pos(rnode)
                # (ii)
                if rnode.tag is etree.Comment:
                    yield actions.InsertComment(
                        utils.getpath(ltarget, ltree), pos, rnode.text
                    )
                    lnode = etree.Comment(rnode.text)
                else:
                    yield actions.InsertNode(
                        utils.getpath(ltarget, ltree), rnode.tag, pos
                    )
                    lnode = ltarget.makeelement(rnode.tag)

                    # (iii)
                self.append_match(lnode, rnode, 1.0)
                ltarget.insert(pos, lnode)
                self._inorder.add(lnode)
                self._inorder.add(rnode)
                # And then we update attributes. This is different from the
                # paper, because the paper assumes nodes only has labels and
                # values. Nodes also has texts, we do them later.
                yield from self.update_node_attr(lnode, rnode)

            # (c)
            else:
                # Normally there is a check that rnode isn't a root,
                # but that's perhaps only because comparing valueless
                # roots is pointless, but in an elementtree we have no such
                # thing as a valueless root anyway.
                # (i)
                lnode = self._r2lmap[id(rnode)]

                # (iii) Move
                lparent = lnode.getparent()
                if ltarget is not lparent:
                    pos = self.find_pos(rnode)
                    yield actions.MoveNode(
                        utils.getpath(lnode, ltree), utils.getpath(ltarget, ltree), pos
                    )
                    # Move the node from current parent to target
                    lparent.remove(lnode)
                    ltarget.insert(pos, lnode)
                    self._inorder.add(lnode)
                    self._inorder.add(rnode)

                # Rename
                yield from self.update_node_tag(lnode, rnode)

                # (ii) Update
                # XXX If they are exactly equal, we can skip this,
                # maybe store match results in a cache?
                yield from self.update_node_attr(lnode, rnode)

            # (d) Align
            yield from self.align_children(lnode, rnode)

            # And lastly, we update all node texts. We do this after
            # aligning children, because when you generate an XML diff
            # from this, that XML diff update generates more children,
            # confusing later inserts or deletes.
            lnode = self._r2lmap[id(rnode)]
            yield from self.update_node_text(lnode, rnode)

        for lnode in utils.reverse_post_order_traverse(self.left):
            if id(lnode) not in self._l2rmap:
                # No match
                yield actions.DeleteNode(utils.getpath(lnode, ltree))
                lnode.getparent().remove(lnode)
