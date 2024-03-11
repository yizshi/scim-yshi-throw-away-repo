from abnf.parser import NodeVisitor, Node
from sync_app.parsers.scim_query_filter import Rule as SCIMQueryRule
from sync_app import exceptions

from typing import List, TypeAlias, Mapping, Tuple, Callable, Type, Sequence

AttributePathSegment: TypeAlias = str
AttributePath = List[AttributePathSegment]
MappingPredicate = Callable[[Mapping], bool]


def get_attribute_from_path(path: AttributePath, resource):
    for segment in path:
        resource = resource.get(segment, None)
        if resource is None:
            return None

    return resource


def set_attribute_in_path(path: AttributePath, resource: dict, value):
    head = path[0]

    if len(path) == 1:
        resource[head] = set_attribute_value(resource.get(head, None), value)
        return

    if head not in resource:
        # we have multiple segments remaining so just create and empty complex attribute
        resource[head] = {}

    return set_attribute_in_path(path[1:], resource[head], value)


def set_attribute_value(attribute, value):
    if isinstance(attribute, dict):
        # complex attribute
        result = dict(attribute)
        result.update(value)
    elif isinstance(attribute, list):
        # multi-valued attribute
        result = list(attribute)
        result.append(value)
    else:
        # single-valued attribute
        result = value

    return result


def delete_attribute_in_path(path: AttributePath, resource: dict):
    head = path[0]

    if len(path) == 1:
        value = resource[head]
        del resource[head]
        return

    if head not in resource:
        # deleting something that doesn't exist is a no-op
        return

    delete_attribute_in_path(path[1:], resource[head])
    if len(resource[head]) == 0:
        del resource[head]


def path_in_resource(path, resource):
    return bool(get_attribute_from_path(path, resource))


def strip_space_nodes(nodes: List[Node]):
    return [n for n in nodes if n.name != "SP"]


class SubattributeQueryExtractor(NodeVisitor):
    @staticmethod
    def parse_filter(query: str):
        try:
            parser = SCIMQueryRule("attributegroup")
            result = parser.parse_all(query)
            visitor = PythonFilter()
            return visitor.visit(result)
        except Exception as e:
            parser = SCIMQueryRule("attributepath")
            result = parser.parse_all(query)
            visitor = PythonFilter()
            return visitor.visit(result), ""

    def visit_attributegroup(self, node) -> Tuple[AttributePath, str]:
        children = strip_space_nodes(node.children)
        path = self.visit(children[0])
        filter = children[2]

        return path, filter.value

    def visit_attributepath(self, node) -> AttributePath:
        # Ignore URL: prefixing for now
        segments = []
        for segment in node.children:
            if segment.name != "attributePathSegment":
                continue

            segments.append(segment.value)

        return segments


class PythonFilter(NodeVisitor):
    @staticmethod
    def parse_filter_to_predicate(filter: str):
        parser = SCIMQueryRule("filter")
        result = parser.parse_all(filter)
        visitor = PythonFilter()
        return visitor.visit(result)

    @staticmethod
    def parse_filter_to_path(query: str) -> AttributePath:
        parser = SCIMQueryRule("attributepath")
        result = parser.parse_all(query)
        visitor = PythonFilter()
        return visitor.visit(result)

    def visit_filter(self, node: Node) -> MappingPredicate:
        assert len(node.children) == 1, "Filters should have only 1 child"
        return lambda r: self.visit(node.children[0])(r)

    def visit_expression(self, node: Node) -> MappingPredicate:
        assert len(node.children) == 1, "Expressions should have only 1 child"
        return lambda r: self.visit(node.children[0])(r)

    def visit_precedencegroup(self, node: Node) -> MappingPredicate:
        children = strip_space_nodes(node.children)
        assert len(children) == 3, "Precdence groups should have exactly 3 children"
        return lambda r: self.visit(children[1])(r)

    def visit_prefixlogicalexpression(self, node: Node) -> MappingPredicate:
        assert (
            node.children[0].value == "not"
        ), "Not is the only valid prefix logical operator"
        # "not" is the only prefix operator
        # last child is always the precedence group
        return lambda r: not self.visit(node.children[-1])(r)

    def visit_infixlogicalexpression(self, node: Node) -> MappingPredicate:
        # must have an odd number of operators
        children_count = len(node.children)
        operations: List[List] = [[node.children[0]]]

        for i in range(1, children_count):
            op = node.children[i].children[1].value
            b = node.children[i].children[3]

            if op == "or":
                operations.append([b])

            elif op == "and":
                operations[-1].append(b)

        return lambda r: any(
            [all([self.visit(ands)(r) for ands in ors]) for ors in operations]
        )

    def visit_infixlogicalexpressionpredicate(self, node: Node):
        assert False, "should never visit a raw logical expression predicate"

    def visit_infixlogicalexpressionoperator(self, node: Node):
        assert False, "should never visit a raw infix logical expression operator"

    def visit_postfixassertion(self, node: Node) -> MappingPredicate:
        path = self.visit(node.children[0])
        assert node.children[2].value == "pr", "PR is the only valid postfix assertion"
        return lambda r: path_in_resource(path, r)

    @staticmethod
    def types_comparable(a, b) -> bool:
        types: Mapping[str, Sequence[Type]] = {
            "string": [str],
            "number": [int, float, complex],
        }

        for type_list in types.values():
            if type(a) in type_list:
                return type(b) in type_list

        return False

    # XXX this is not correctly handling caseExact specifications
    # case exact for
    # id
    # externalId
    # meta.resourceType
    # meta.version
    # schema in ResourceType
    # schemaExtensions in ResourceType
    # attributes.*.name in Schema (attribute names)
    # attributes.*.description in Schema (attribute descriptions)
    # attributes.*.mutability in Schema (attribute mutability)
    # attributes.*.returned in Schema (attribute returned)
    # attributes.*.uniqueness in Schema (attribute uniqueness)
    # attributes.*.referenceTypes in Schema (attribute referenceTypes)
    # attributes.*.subAttributes.name in Schema
    # attributes.*.subAttributes.description in Schema
    # attributes.*.subAttributes.canonicalValues in Schema
    # attributes.*.subAttributes.mutability in Schema
    # attributes.*.subAttributes.returned in Schema
    # attributes.*.subAttributes.returned in Schema
    # attributes.*.subAttributes.referenceTypes in Schema

    def visit_infixassertion(self, node: Node) -> MappingPredicate:
        path: AttributePath = self.visit(node.children[0])
        operator = node.children[2].value
        value = self.visit(node.children[4])

        def comparison(r):
            attribute_value = get_attribute_from_path(path, r)
            if operator == "eq":
                return attribute_value == value

            elif operator == "ne":
                return attribute_value != value

            elif value is None or attribute_value is None:
                # always reject attributes with None except for equality checks
                # I would consider making this illegal in the grammar
                return False

            elif not self.types_comparable(attribute_value, value):
                raise exceptions.InvalidSCIMFilter(
                    f"Attribute value could not be compared to filter with the specified operation {attribute_value}, {value}"
                )

            elif operator == "gt":
                return attribute_value > value

            elif operator == "lt":
                return attribute_value < value

            elif operator == "ge":
                return attribute_value >= value

            elif operator == "le":
                return attribute_value <= value

            elif isinstance(value, (int, float, complex)) or isinstance(
                attribute_value, (int, float, complex)
            ):
                # might want to return a filter error here?
                # for now reject numbers from string operations
                # I would consider making this illegal in the grammar
                return False

            elif operator == "co":
                return value in str(attribute_value)

            elif operator == "sw":
                return str(attribute_value).startswith(value)

            elif operator == "ew":
                return str(attribute_value).endswith(value)

        return comparison

    def visit_infixassertionvalue(self, node: Node) -> MappingPredicate:
        assert len(node.children) == 1, "Infix assertions should only have one child"
        return self.visit(node.children[0])

    def visit_attributepath(self, node: Node) -> AttributePath:
        # Ignore URL: prefixing for now
        segments = []
        for segment in node.children:
            if segment.name != "attributePathSegment":
                continue

            segments.append(segment.value)

        return segments

    def visit_attributegroup(self, node: Node) -> MappingPredicate:
        children = strip_space_nodes(node.children)
        path = self.visit(children[0])
        filter = children[2]

        def subquery(r):
            attribute_value = get_attribute_from_path(path, r)
            subpredicate = self.visit(filter)
            return subpredicate(attribute_value)

        return subquery

    def visit_attributepathsegment(self, node: Node) -> AttributePathSegment:
        return str(node.value)

    def visit_false(self, _) -> bool:
        return False

    def visit_null(self, _) -> None:
        return None

    def visit_true(self, _) -> bool:
        return True

    def visit_number(self, node: Node) -> float:
        return float(node.value)

    def visit_string(self, node: Node) -> str:
        return str(node.value[1:-1])
