from typing import TypeVar

T = TypeVar("T", int, str)


def detect_circles(
    check_list: set[T],
    relevant_tree: dict[T, T | None] | dict[T, tuple[T | None, list[T]]],
) -> set[T]:
    """
    Detects circles in the relevant_tree and returns all elements that are part of them.
    relevant_tree is expected to be a child-to-parent dict.
    Optionally the values of the dict may be (parent, empty list) tuples.
    In this case the list will be dynamically filled with the children of each entry
    """
    circle_related: set[T] = set()
    free: set[T] = set()
    circles: set[T] = set()
    while check_list:
        entry = check_list.pop()
        descendants: list[T] = [entry]
        data = relevant_tree[entry]
        parent: T | None = data[0] if isinstance(data, tuple) else data
        while parent:
            if isinstance(
                parent_data := (
                    relevant_tree[parent] if parent in relevant_tree else None
                ),
                tuple,
            ):
                parent_data[1].append(entry)
            if parent in circle_related:
                circle_related.update(descendants)
                break
            if parent in free:
                free.update(descendants)
                break
            if parent in descendants:
                index = descendants.index(parent)
                circle_related.update(descendants)
                circles.update(descendants[index:])
                break
            descendants.append(parent)
            entry = parent
            data = parent_data
            parent = data[0] if isinstance(data, tuple) else data
        check_list.difference_update(descendants)
    return circles
