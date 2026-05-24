# -*- coding: utf-8 -*-

class MinHeap:
    """
    Custom Min-Heap (Priority Queue) triển khai thủ công không dùng thư viện 'heapq'.
    Lưu trữ các phần tử dưới dạng tuple: (key, value)
    """
    def __init__(self):
        self.heap = []

    def push(self, key, value):
        """Thêm một phần tử mới vào Heap và thực hiện vun đống từ dưới lên."""
        self.heap.append((key, value))
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """Lấy và xóa phần tử có 'key' nhỏ nhất ra khỏi Heap, sau đó vun đống từ trên xuống."""
        if self.is_empty():
            raise IndexError("Lỗi: Không thể pop từ một Heap rỗng.")
        
        if len(self.heap) == 1:
            return self.heap.pop()

        root = self.heap[0]
        # Đưa phần tử cuối cùng lên làm gốc và loại bỏ phần tử cuối khỏi mảng
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return root

    def peek(self):
        """Xem phần tử nhỏ nhất hiện tại mà không xóa nó."""
        if self.is_empty():
            return None
        return self.heap[0]

    def is_empty(self):
        """Kiểm tra Heap rỗng."""
        return len(self.heap) == 0

    def __len__(self):
        return len(self.heap)

    def _heapify_up(self, index):
        """Cân bằng Heap theo chiều từ dưới lên (Sift-up)."""
        parent = (index - 1) // 2
        while index > 0 and self.heap[index][0] < self.heap[parent][0]:
            # Hoán vị nếu node con nhỏ hơn node cha
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            index = parent
            parent = (index - 1) // 2

    def _heapify_down(self, index):
        """Cân bằng Heap theo chiều từ trên xuống (Sift-down)."""
        length = len(self.heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            # So sánh với con bên trái
            if left < length and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            # So sánh với con bên phải
            if right < length and self.heap[right][0] < self.heap[smallest][0]:
                smallest = right

            # Nếu node cha không phải là nhỏ nhất, tiến hành hoán vị và lặp tiếp
            if smallest != index:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
            else:
                break