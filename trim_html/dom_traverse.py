from bs4 import BeautifulSoup
from bs4.element import NavigableString
import logging
import copy

class DomParser:
    def __init__(self, _dom_element, _parent, _idx):
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
        self.is_leaf = (len(self.dom_element.findChildren()) == 0)
        self.idx = _idx
        #self.removed_attr_key = None
        #self.removed_attr_value = None

    def replace_str(self, idx, new_str):
        '''
        replace string

        Args:
            idx: replaced str in idx_th contents
            new_str: replaced string

        Returns:
            The replaced NavigableString
        '''
        str_replaced = self.dom_element.contents.pop(idx)
        logging.debug('replaced string %s with %s' % (repr(str_replaced), new_str))
        self.dom_element.contents.insert(idx, NavigableString(new_str))
        return str_replaced

    def recover_replace_str(self, idx, replaced_str):
        '''
        recover replaced string
        Args:
            idx: recovered str in idx_th contents
            replaced_str: replaced string

        Returns:
            None
        '''
        str_replaced = self.dom_element.contents.pop(idx)
        logging.debug('recover replaced string %s with %s' %\
                (repr(str_replaced), repr(replaced_str)))
        self.dom_element.contents.insert(idx, replaced_str)

    def remove_str(self, idx):
        '''
        remove string of dom_element

        Args:
            idx: removed str in idx_th contents

        Returns:
            removed NavigableString
        '''
        str_removed = self.dom_element.contents.pop(idx)
        logging.debug('removing string %s' % repr(str_removed))
        return str_removed

    def recover_str(self, idx, str_recoved):
        '''
        recover string of dom_element

        Args:
            idx: index of recovered
            str_recovered: recovered NavigableString Object
        '''
        logging.debug('recoving string %s' % repr(str_recoved))
        self.dom_element.contents.insert(idx, str_recoved)

    def remove_attr(self, key):
        '''
        remove attribute of _dom_element

        Args:
            key: key of removed attribute

        Returns:
            removed value of attribute
        '''
        logging.debug('removing attribute %s' % key)
        if key not in self.dom_element.attrs:
            logging.error('key %s is not in %s attributes' \
                    % (key, repr(self.dom_element)))
            return None

        return self.dom_element.attrs.pop(key)

    def recover_attr(self, key, value):
        '''
        recover attribute of _dom_element

        Args:
            key: key of added attribute
            value: value of added attribute
        '''
        logging.debug('recovering attribute %s: %s' % (key, value))
        self.dom_element.attrs[key] = value

    def remove_child_element(self):
        """
        remove one child element from current dom element

        Args:
            child_element: child element that to be deleted

        Returns:
            None
        """
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
        self.parent.insert(self.idx, self.dom_element)

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
