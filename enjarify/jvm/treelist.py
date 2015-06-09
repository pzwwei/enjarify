# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The first SIZE elements are stored directly, the rest are stored in one of SPLIT subtrees
SIZE = 16
SPLIT = 2

# This class represents a list as a persistent n-ary tree
# This has much slower access and updates than a real list but has the advantage
# of sharing memory with previous versions of the list when only a few elements
# are changed. See http://en.wikipedia.org/wiki/Persistent_data_structure#Trees
# Also, default values are not stored, so this is good for sparse arrays
class ImmutableTreeList:
    def __init__(self, default, direct=None, children=None):
        self.default = default
        if direct is None:
            self.direct = [self.default]*SIZE
            self.children = [None]*SPLIT # Subtrees allocated lazily
        else:
            self.direct = direct
            self.children = children

    def __getitem__(self, i):
        assert(i >= 0)
        if i < SIZE:
            return self.direct[i]

        i -= SIZE
        i, ci = divmod(i, SPLIT)
        child = self.children[ci]

        if child is None:
            return self.default
        return child[i]

    def set(self, i, val):
        assert(i >= 0)
        if i < SIZE:
            if self.direct[i] == val:
                return self

            temp = self.direct[:]
            temp[i] = val
            return ImmutableTreeList(self.default, temp, self.children)

        i -= SIZE
        i, ci = divmod(i, SPLIT)
        child = self.children[ci]

        if child is None:
            if val == self.default:
                return self
            child = ImmutableTreeList(self.default).set(i, val)
        else:
            if val == child[i]:
                return self
            child = child.set(i, val)

        temp = self.children[:]
        temp[ci] = child
        return ImmutableTreeList(self.default, self.direct, temp)

    @staticmethod
    def merge(left, right, func):
        # Effectively computes [func(x, y) for x, y in zip(left, right)]
        # Assume func(x, x) == x
        if left is right:
            return left

        if left is None:
            left, right = right, left

        default = left.default
        merge = ImmutableTreeList.merge
        if right is None:
            direct = [func(x, default) for x in left.direct]
            children = [merge(child, None, func) for child in left.children]
            if direct == left.direct and children == left.children:
                return left
            return ImmutableTreeList(default, direct, children)

        direct = [func(x, y) for x, y in zip(left.direct, right.direct)]
        children = [merge(c1, c2, func) for c1, c2 in zip(left.children, right.children)]
        if direct == left.direct and children == left.children:
            return left
        if direct == right.direct and children == right.children:
            return right
        return ImmutableTreeList(default, direct, children)