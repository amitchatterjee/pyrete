from decimal import Decimal

class Element:
    def __init__(self, prev, next, obj, ord):
        self.prev = prev
        self.next = next
        self.obj = obj
        self.ord = ord

    def __str__(self):
        return f"Element:({self.obj})"

class Graph:
    def __init__(self, comparator):
        self.first = None
        self.cursors = {}
        self.comparator = comparator

    def __ordinal(self, prev, next):
        p_ordinal = prev.ord if prev else Decimal(0)
        n_ordinal = next.ord if next else p_ordinal + Decimal(100)
        return (p_ordinal + n_ordinal) / Decimal(2)

    def insert(self, obj):
        if not self.first:
            # If this is the only element in the list
            node = Element(None, None, obj, self.__ordinal(None,None))
            self.first = node
            return node
        
        last = None
        element = self.first
        while element:
            # Invoke the comparator.
            result = self.comparator(obj, element.obj)
            if result < 0:
                # The obj needs to be inserted left of the element
                prev = element.prev
                next = element.next
                node = Element(prev, element, obj, self.__ordinal(prev,element))
                if prev:
                    prev.next = node
                else:
                    self.first = node
                if next:
                    next.prev = node
                return node
            last = element
            element = element.next

        # Insert it at the rightmost side of the list
        node = Element(last, None, obj, self.__ordinal(last, None))
        last.next = node
        return node

    def delete(self, obj):
        element = self.first
        while element:
            if obj == element.obj:
                next = self.delete_element(element)

                return True, next
            element = element.next
        # Element is not found
        return False, None

    def delete_element(self, element):
        prev = element.prev
        next = element.next
        if prev:
            if next:
                # Removing an element between two elements
                prev.next = next
                next.prev = prev
            else:
                # Removing an element that is at the end of the list
                prev.next = None
        else:
            if next:
                # Removing an element that at the beginning of the list
                next.prev = None
                self.first = next
            else:
                # Removing the only element from the list
                self.first = None

        for name,cursor in self.cursors.items():
            if element == cursor:
                # If this element is currently being iterated on, move the pointer forward
                self.cursors[name] = next
        return next

    def new_cursor(self, cursor_name = 'default', node = None):
        if not node:
            self.cursors[cursor_name] = self.first
        else:
            self.cursors[cursor_name] = node

    def get_cursor(self, cursor_name = 'default'):
        return self.cursors[cursor_name]

    def next(self, cursor_name = 'default'):
        cursor = self.next_element(cursor_name)
        if not cursor:
            return None
        return cursor.obj
    
    def next_element(self, cursor_name = 'default'):
        cursor = self.cursors[cursor_name]
        if not cursor:
            return None
        self.cursors[cursor_name] = cursor.next
        return cursor
    
    def compare(self, node1, node2):
        return node1.ord - node2.ord

    def is_left_of(self, node, cursor_name = 'default'):
        return self.compare(self.cursors[cursor_name], node) < 0
        
    def is_right_of(self, node, cursor_name = 'default'):
        return self.compare(self.cursors[cursor_name], node) > 0
    
    def is_on_node(self, node, cursor_name = 'default'):
        return self.compare(self.cursors[cursor_name], node) == 0