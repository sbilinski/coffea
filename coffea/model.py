#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2013 Szymon Biliński 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import abc
import logging
import threading

log = logging.getLogger('model')

class Model(object):
    """A thread-safe data model abstraction."""

    def __init__(self):
        """Initializes a new instance of the Model class."""
        
        self._lock = threading.Lock()
        self.nodes = []
        self.node_filters = []
            
    def merge(self, node):
        """Merges provided Node into the underlying graph."""
    
        for nf in self.node_filters:
            assert isinstance(nf, NodeFilter), 'Node filter expected. Got: %s' % type(nf)
            node = nf(node)
            if node == None:
                log.debug('Node rejected by: %s', nf)
                return            
            assert isinstance(node, Node), 'Node expected. Got: %s' % type(node)
       
        self._lock.acquire()
       
        #TODO: Find *first* occurrence 
        existing = filter(lambda it: it.id == node.id, self.nodes)
        if existing:
            existing=existing[0]

            for new_conn in node.connections:
                existing.connections.add(new_conn)
        else:
            self.nodes.append(node)
        
        self._lock.release()


class Node(object):
    """A graph node."""

    def __init__(self, node_id, connections=[]):
        """Initializes a new instance of the Node class."""
        self.id = node_id
        self.connections = set(connections)

    def __repr__(self):
        """Returns a string representation of the object."""
        return str(self.id)


class NodeFilter(object):
    """Abstract base class for model node filters."""
    __metaclass__ = abc.ABCMeta

    def __call__(self, node):
        """Delegates to self.filter_node(node)."""
        return self.filter_node(node)

    @abc.abstractmethod
    def filter_node(self, node):
        """Returns a processed instance of node or None, if it should be dropped."""
        return node


class NodeIdFilter(NodeFilter):
    """Filters IDs using an external function."""
     
    def __init__(self, id_filter_function):
        """Initializes a new instance of the NodeIdFilter class."""
        
        self._id_filter = id_filter_function 
        self._drop_count = 0
         
    def filter_node(self, node):
        assert self._id_filter
        if not self._id_filter(node.id):
            self._drop_count += 1
            return None
        node.connections = set(filter(self._id_filter, node.connections)) 
        return node


class NodeIdMapper(NodeFilter):
    """Maps IDs using an external function."""
    
    def __init__(self, id_map_function):
        """Initializes a new instance of the NodeIdMapper class."""
        
        self._id_mapper = id_map_function
        self._map_count = 0 
        
    def filter_node(self, node):
        assert self._id_mapper 
        node.id = self._id_mapper(node.id) 
        node.connections = set(map(self._id_mapper, node.connections))
        self._map_count += 1
        return node
