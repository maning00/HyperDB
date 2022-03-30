from typing import List, Union, Tuple
from random import random
from hashlib import sha256
from typing import Union
import binascii


def hash_fun(x: bytes, y: bytes) -> bytes:
    return sha256(bytes(binascii.a2b_hex(min(x.hex(), y.hex()) + max(x.hex(), y.hex())))).digest()


class AuthenticResponse:
    def __init__(self, timestamp: bytes, item, proof, result: bool):
        self.timestamp = timestamp.hex()
        self.item = item.hex()
        ls = [x.hex() for x in proof]
        self.proof = ls
        self.result = result

    def subject_contained(self):
        return self.result

    def validates_against(self, timestamp: Union[bytes, None] = None):
        if timestamp is None:
            timestamp = self.timestamp
        acc = binascii.a2b_hex(self.proof[0])
        for value in self.proof[1:]:
            acc = hash_fun(acc, binascii.a2b_hex(value))
        return timestamp == acc


class Node:
    def __init__(self, item, height: int = 1):
        self.item = item
        self.height = height
        self.refs: List[Union[Node, None]] = [None] * height
        self.hashes: List[Union[bytes, None]] = [None] * height

    def compute_hashes(self) -> None:
        for i in range(self.height):
            self.hashes[i] = self.compute_hash(i)

    def compute_hash(self, index) -> bytes:
        if self.refs[index] is None:
            return hash_fun(SkipList.zero, SkipList.zero)
        else:
            if index == 0:
                w = self.refs[index]
                if w.height - 1 > index:
                    return hash_fun(bytes(self.item), bytes(w.item))
                else:
                    return hash_fun(bytes(self.item), w.hashes[index])
            else:
                w = self.refs[index]
                if w.height - 1 > index:
                    return self.hashes[index - 1]
                else:
                    return hash_fun(self.hashes[index - 1], w.hashes[index])

    def __str__(self):
        return "Node<" + str(self.item) + ">"


class SkipList:
    seed = b'\xd1\xf7\xb7\xd5\xa6\xbd\xef^\x9f\xeb\xcfy\xe9\xff\x1d\xef\xc7|m\xd7\xb7\xf5\xc6\xbay\xde]\xe7\xbe\xf5' \
           b'\xe7w]\xe1\xf7\xfc\xeb\xa6\x9a\xe9\xf7\x1d}\xde\xfb\xd9\xee\x9a'
    zero = b'{N\xbay\xf7\xb5\xe5\xd6\xde\xdb\xce\xf5\xef\x87{\xe3\xdf\x1em\xf7\x1bw\xa7=m\xd6\xfc\xf7\xb6\xbc' \
           b'\xdb\xbex\xeb~:\xdd\xfft\xef\x96\xfdi\xf7_\xf3\x9e\x1f'

    def __init__(self):
        self.tail: Node = Node(self.zero, 2)
        self.tail.compute_hashes()
        self.head: Node = Node(self.seed)
        self.head.refs[0] = self.tail
        self.head.compute_hashes()

        self.length: int = 0
        self.level: int = 1
        self.timestamp: bytes = self.head.hashes[0]

    def __len__(self):
        return self.length

    def __str__(self):
        l = []
        node = self.head
        while node is not None:
            l.append((node.item, list(map(lambda r: "None" if r is None else r.item, node.refs))))
            node = node.refs[0]
        return "Skiplist<" + str(l) + ">"

    def __head_hash(self) -> bytes:
        return self.head.hashes[self.level - 1]

    @staticmethod
    def __gen_height(_height: Union[int, None]) -> int:
        if _height is not None:
            return _height
        height = 1
        while random() < 0.5:
            height += 1
        return height

    def __find_node(self, item) -> Node:
        node = self.head
        height = self.level - 1
        while height >= 0:
            next = node.refs[height]
            if next is not self.tail and next.item <= item:
                node = next
            else:
                height -= 1
        return node

    def __find_update(self, item) -> List[Node]:
        node = self.head
        update: List[Union[Node, None]] = [None] * self.level
        height = self.level - 1
        while height >= 0:
            next = node.refs[height]
            if next is not self.tail and next.item < item:
                node = next
            else:
                update[height] = node
                height -= 1
        return update

    def contains(self, item) -> bool:
        return self.__find_node(item).item == item

    __contains__ = contains

    def insert(self, item, _height: Union[int, None] = None) -> None:
        height = self.__gen_height(_height)

        head = self.head
        tail = self.tail
        before = head.height
        if before < height:
            tail.height = height + 1
            head.height = height
        for i in range(before, height):
            tail.refs.append(None)
            tail.hashes.append(tail.compute_hash(i))
            head.refs.append(self.tail)
            head.hashes.append(head.compute_hash(i))

        if self.level < height:
            self.level = height

        update = self.__find_update(item)
        p = self.__get_p(item)
        node = Node(item, height)
        for i in range(height):
            node.refs[i] = update[i].refs[i]
            update[i].refs[i] = node

        node.compute_hashes()
        for n, h in p.__reversed__():
            n.hashes[h] = n.compute_hash(h)

        for i in range(before, height):
            head.hashes[i] = head.compute_hash(i)
        self.length += 1

    def delete(self, item):
        if self.length == 0:
            return None

        update = self.__find_update(item)
        p = self.__get_p(item)
        node = update[0].refs[0]
        if node is not None and node.item == item:
            for i in range(node.height):
                update[i].refs[i] = node.refs[i]
            while self.level > 1 and self.head.refs[self.level - 1] is self.tail:
                self.level -= 1
            self.length -= 1
            for n, h in p.__reversed__():
                n.hashes[h] = n.compute_hash(h)
            return item

        return None

    def __get_p(self, item) -> List[Tuple[Node, int]]:
        update = self.__find_update(item)
        p: List[Tuple[Node, int]] = []
        node = self.head
        for i in range(len(update) - 1, -1, -1):
            while node is not update[i]:
                p.append((node, i))
                node = node.refs[i]
            p.append((node, i))
        return p

    def update(self, insertion: bool, item, timestamp: Union[bytes, None] = None, height: Union[int, None] = None)\
            -> None:
        if insertion:
            self.insert(item, height)
        else:
            self.delete(item)

        if timestamp is None:
            timestamp = self.__head_hash()
        self.timestamp = timestamp

    def verify(self, item) -> AuthenticResponse:
        p = self.__get_p(item)
        p.append((p[-1][0].refs[0], 0))

        plen = len(p)
        q = []
        wv, _ = p.pop()
        zw = wv.refs[0]
        if wv.height == 1:
            if zw.height == 1:
                q.append(zw.hashes[0])
            else:
                q.append(zw.item)
        q.append(wv.item)
        result = wv.item == item
        j = 1
        pv = wv
        for i in range(1, plen):
            v, h = p.pop()
            w = v.refs[h]
            if h == 0 or w.height - 1 == h:
                j += 1
                if w is not pv:
                    q.append(w.hashes[h])
                else:
                    if h == 0:
                        q.append(v.item)
                    else:
                        q.append(v.hashes[h - 1])
            pv = v
        return AuthenticResponse(self.timestamp, item, q, result)
