"""Small graph helpers: strongly connected components (cycles) and shortest cycle paths.

Everything is deterministic: nodes and neighbours are always visited in sorted order. The component
search is iterative, so a very large inventory cannot hit the recursion limit.
"""

from __future__ import annotations

from collections import deque


def strongly_connected_components(nodes, edges):
    """Tarjan's algorithm. `edges` maps node to an iterable of nodes it points to.

    Returns a list of components, each a sorted list of nodes, ordered by their smallest member.
    A single node with no self loop is returned as a one-member component.
    """
    nodes = sorted(nodes)
    adj = {n: sorted(set(edges.get(n, ())) & set(nodes)) for n in nodes}
    index, low, on_stack, stack, result = {}, {}, set(), [], []
    counter = 0
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(adj[root]))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(adj[child])))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    comp.append(member)
                    if member == node:
                        break
                result.append(sorted(comp))
    result.sort(key=lambda c: c[0])
    return result


def shortest_cycle_through(start, members, edges):
    """Shortest path start -> ... -> start inside `members`, as a list ending with `start`.

    Used to show one concrete loop for a component. Returns None if there is no such loop.
    """
    allowed = set(members)
    queue = deque([(start, [start])])
    seen = set()
    while queue:
        node, path = queue.popleft()
        for nxt in sorted(set(edges.get(node, ())) & allowed):
            if nxt == start:
                return path + [start]
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt]))
    return None
