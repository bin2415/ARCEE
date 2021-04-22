from bs4 import BeautifulSoup
import logging
import copy

class DomParser:
    def __init__(self, _dom_element, _parent):
        """
        initialization of DomParser

        Args:
            _dom_element: dom element

        self.children: list. store all children elements
        self.parent: dom element
        self.parent_copy: deep copy of its parent
        self.traversed: if current node has been traversed
        self.is_leaf: if current node is a leaf node
        """
        self.dom_element = _dom_element
        self.children = list()
        self.parent = _parent
        self.parent_copy = None
        self.is_leaf = (len(self.dom_element.findChildren()) == 0)

    def remove_child_element(self):
        """
        remove one child element from current dom element

        Args:
            child_element: child element that to be deleted

        Returns:
            None
        """
        if not self.parent_copy:
            self.parent_copy = copy.deepcopy(self.parent)

        logging.debug('removing %s' % str(self.dom_element))
        if self.dom_element != None:
            self.dom_element.extract()

    def recover_child_element(self):
        """
        recover one child element from current dom element

        Args:
            child_element: child element that to be recovered

        Returns:
            None
        """
        logging.debug('recoving %s' % str(self.parent_copy))
        self.parent.replace_with(self.parent_copy)
        self.parent = self.parent_copy
        self.parent_copy = None

    def recursive_parse(self):
        """
        recursively parse current dom tree

        Args:
            None

        Returns:
            None
        """
        if self.is_leaf:
            return

        for child in self.dom_element.findChildren():
            self.children.append(DomParser(child, self.dom_element))

        for child in self.children:
            child.recursive_parse()
