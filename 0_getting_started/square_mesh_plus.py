import numpy as np
sqrt3 = 3**0.5
#这个脚本是为了实现等边三角形的网络而编写的。

# 0-based 三角行优先索引：第 i 层有 n_seg+1-i 个节点
# index = f(i,j,n) = (2*n+3-i)*i/2+j
def ind(i, j, n):
    return (2 * n + 3 - i) * i // 2 + j

def generate(side_length, n_seg):
    # 等边三角形每条边分 n_seg 段，总节点数为 1/2 * (n_seg+1) × (n_seg+2)
    n_nodes = (n_seg + 1) * (n_seg + 2) // 2
    x = np.zeros((n_nodes, 2))
    step = side_length / n_seg  # 步长
    # 以等边三角形最左边的顶点为原点建立坐标系，这样等边三角形所有的点都是在第一象限。
    # i 代表被分割后的等边三角形的层数，从第 0 层到第 n_seg 层（共 n_seg+1 层）。
    for i in range(0, n_seg + 1):
        for j in range(0, n_seg + 1 - i):
            x[ind(i, j, n_seg)] = [0.5 * i * step + j * step, 0.5 * sqrt3 * i * step]

    # connect the nodes with edges
    e = []
    for i in range(0, n_seg):
        for j in range(0, n_seg - i + 1):
            if j != n_seg - i:
                e.append([ind(i, j, n_seg), ind(i, j + 1, n_seg)])      # 水平边
                e.append([ind(i, j, n_seg), ind(i + 1, j, n_seg)])      # 右上边
            if j != 0:
                e.append([ind(i, j, n_seg), ind(i + 1, j - 1, n_seg)])  # 左上边

    return [x, e]
