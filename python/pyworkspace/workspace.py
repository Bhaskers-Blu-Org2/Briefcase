import os
from typing import Any, Callable, List, Union, Type
import re
import yaml

# TODO: check if the imports are needed
from .azure import *
from .azure.cognitiveservice import *
from .base import *
from .datasource import *
from .credentialprovider import *

class Workspace:
    def __init__(self, path: str=None, content: str=None):
        # TODO: think about multiple yamls and when to actually stop
        # force user to supply path
        # stop at .git directory (what about .svn?)

        # handle various defaults
        if content is None:
            if path is None:
                path = self.__find_yaml('.')
            
            with open(path, 'r') as f:
                content = f.read()

        self.__parse(content)

    def __find_yaml(self, path) -> str:   
        path = os.path.realpath(path)

        for name in os.listdir(path):
            # TODO: allow for different name. global param? ctor param?
            if name == 'resources.yaml' or name == 'resources.yml':
                return os.path.join(path, name)

        # going up the directory structure
        new_path = os.path.realpath(os.path.join(path, '..'))
        if path == new_path: # hit the root
            raise Exception("Unable to find resources.yaml")

        return self.__find_yaml(new_path)

    def __parse(self, content: str):
        # TODO: don't fail for future types. the safe_load thing is the right approach, but
        #       this will lead to failures ones new types are introduced and the workspace library
        #       is still old... 

        # Still loading using SafeLoader, but making sure unknown tags are ignored
        # https://security.openstack.org/guidelines/dg_avoid-dangerous-input-parsing-libraries.html
        # self.resources = yaml.safe_load(content)

        class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
            def ignore_unknown(self, node):
                return None 
        
        SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)
        self.resources = yaml.load(content, Loader=SafeLoaderIgnoreUnknown)

        # visit all nodes and setup links
        def setup_links(node, path, name):
            node.__workspace = self
            node.__path = path
            node.__name = name        

        # setup root links to avoid back reference to credential provider
        self.visit(setup_links)

    def visit(self,
              action: Callable[[yaml.YAMLObject, List[str], str], Any],
              path: List[str] = [],
              node: Any = None) -> List:
        if node is None:
            node = self.resources

        ret = []
        for k, n in node.items():
            if isinstance(n, dict):
                ret.extend(self.visit(action, [*path, k], n))
            elif isinstance(n, yaml.YAMLObject):
                v = action(n, path, k) 
                if v is not None:
                    ret.append(v)

        return ret

    def get_all_of_type(self, type: Type):
        return self.visit(lambda node, _, __: node if isinstance(node, type) else None)

    key_split_regex = re.compile('[./]')

    def __getitem__(self, key: str) -> Union[Resource, List[Resource]]:
        path = Workspace.key_split_regex.split(key)

        if len(path) == 1:
            # search all
            ret = self.visit(lambda node, _, name: node if name == key else None)
            ret_len = len(ret)

            # make it convenient
            if ret_len == 0:
                return None
            elif ret_len == 1:
                return ret[0]
            else:
                ret
        else:
            # if it's a path find the precise one
            node = self.resources
            for name in path:
                node = node[name]
            return node