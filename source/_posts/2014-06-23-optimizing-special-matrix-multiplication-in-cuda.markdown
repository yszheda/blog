---
layout: post
title: "加速CUDA中的一类特殊矩阵乘法"
date: 2014-06-23 20:56
comments: true
categories: [CUDA, tech, CS]
keywords: CUDA, GPGPU, GPU, 矩阵乘法, Reed-Solomon, Galois Field, matrix multiplication, c++, c, template, cuBLAS, MAGMA
description: Optimizing Special Matrix Multiplication in CUDA
---
矩阵乘法是利用GPU加速一般运算的经典范例，在NVIDIA官方的[CUDA C Programming Guide](http://docs.nvidia.com/cuda/cuda-c-programming-guide)和[CUDA C Best Practices Guide](http://docs.nvidia.com/cuda/cuda-c-best-practices-guide)也都有示范代码来说明如何加速矩阵乘法。本渣这里要介绍的是如何加速矩阵乘法的一类特殊情况——大小悬殊的两个矩阵的乘法。

这里稍稍碎碎念一会，其实这个主题主要来自本渣的论文，而本渣所做的主要是用GPU来加速Reed-Solomon Codes的编解码。这种编解码的过程是矩阵乘法，照例说可以直接使用[cuBLAS](https://developer.nvidia.com/cublas)等实现矩阵乘法的CUDA library来做。但由于Reed-Solomon Codes所用到的运算都是定义在伽罗华域（Galois Field）中的，不同于普通的实数运算，所以无法直接调用[cuBLAS](https://developer.nvidia.com/cublas)等library。不巧，这些library所开放的API又不允许operator overloading，再加上矩阵乘法的source code也没有开源（[MAGMA](http://icl.cs.utk.edu/magma/)倒是个<del>open source</del>公布了代码的library，但是它对矩阵乘法的实现只是调用[cuBLAS](https://developer.nvidia.com/cublas)的函数、外加优化某些特殊情况罢了），这使得本渣需要自力更生去琢磨如何加速Reed-Solomon Codes编解码的矩阵乘法。在完成实现之后，本渣发现不少技术细节不足以登学术论文的大雅之堂，于是就想把它们记录进这篇技术文章中。
在我们的Reed-Solomon Codes的实际应用场景中，用到的是以8-bit byte为一个数值单位的矩阵，矩阵乘法通常是一个小矩阵乘以一个扁长的大矩阵的形式：小矩阵的行数和列数一般不超过三位数，大矩阵的行数即为小矩阵的列数，而大矩阵的列数一般大于百万的数量级。
虽然本渣的优化主要根据这些实际情况来做，但优化的技巧仍可以拓展到一般的小矩阵乘以大矩阵的情况的。
<!--
大小悬殊的两个矩阵进行相乘，因此本渣的优化也主要针对小矩阵乘以大矩阵这种矩阵乘法的特殊情况。
-->

在介绍本渣<del>独特</del>的优化技巧之前，让我们先从最简单的做法回顾起：

<!-- more -->

## 最naive的实现 ##

下图显示了矩阵乘法的最一般做法：

{% img /images/mm-CUDA/without-tiling.png %}

CUDA pseudo-code如下：

```c++
// input matrix A and B, compute product matrix C
// A: A_height x A_width
// B: A_width x B_width
// C: A_height x B_width
__global__ void matrix_mul(unsigned char *A, unsigned char *B, unsigned char *C, int A_height, int A_width, int B_width)
{
	int bx = blockIdx.x;
	int by = blockIdx.y;
	int tx = threadIdx.x;
	int ty = threadIdx.y;
	int row, col;
    // 由于矩阵B列的数目远大于GPU的grid size，所以需要以下的while循环。
	do {
		unsigned char product = 0;
		row = by * blockDim.y + ty;
		col = bx * blockDim.x + tx;
		if (row < A_height && col < B_width) {
			for (int i = 0; i < A_width; i++) {
				// 这里姑且假设+和*这两个operator已被overload成Galois Field的加法和乘法。
				product += A[row * A_width + i] * B[i * B_width + col];
			}
			C[row * B_width + col] = product;
		}
		bx += gridDim.x;
		col = bx * blockDim.x + tx;
	} while (col < B_width);
}
```

这种最一般的做法不好的原因，一方面是因为矩阵的元素（也就是图中绿色的小方格）是存在GPU的global memory（global memory其实是off-chip的DRAM，access它需要400到800cycles）之中的，而这种做法需要大量access这些元素，因而也造成了大量的global memory transactions；另一方面，这种做法在access矩阵B的元素用了column major的方式，这种方式的locality差，会导致较高的cache missrate。

## Square-Tiling Algorithm ##

针对最一般的做法的优化是一种很普遍的算法，有的文献（如Hennessy and Patterson的经典教材《Computer Architecture: A Quantitative Approach》）称为blocking，有的（如CUDA的offical guide）称之为tiling。如下图所示，黄色正方形被称为tile，因此我们这里也称这种algorithm为square-tiling算法。

{% img /images/mm-CUDA/square-tiling.png %}

CUDA pseudo-code如下，在CUDA offical guide上也可以看到类似范例：

```c++
// input matrix A and B, compute product matrix C
// A: A_height x A_width
// B: A_width x B_width
// C: A_height x B_width
__global__ void matrix_mul(unsigned char *A, unsigned char *B, unsigned char *C, int A_height, int A_width, int B_width)
{
	// TILE_SIZE是一个macro
	__shared__ unsigned char rowVector[TILE_SIZE][TILE_SIZE];
	__shared__ unsigned char colVector[TILE_SIZE][TILE_SIZE];
	int bx = blockIdx.x;
	int by = blockIdx.y;
	int tx = threadIdx.x;
	int ty = threadIdx.y;
	int row, col;
    // 由于矩阵B列的数目远大于GPU的grid size，所以需要以下的while循环。
	do {
		unsigned char product = 0;
		row = by * TILE_SIZE + ty;
		col = bx * TILE_SIZE + tx;
		__syncthreads();

		if (row < A_height && col < B_width) {
			// TILE_SIZE可能比A的宽度大，所以需要额外引入bound这个变量来保证不越界。
			for (int i = 0; i < (int) (ceil((float) A_width / TILE_SIZE)); i++) {
				int bound = min(A_width, TILE_SIZE);
				for (int j = tx; j < bound; j += blockDim.x) {
					rowVector[ty][j] = A[row * A_width + i * bound + j];
				}
				for (int j = ty; j < bound; j += blockDim.y) {
					colVector[j][tx] = B[col + (i * bound + j) * B_width];
				}
				__syncthreads();
				for (int j = 0; j < bound; j++) {
					// 这里姑且假设+和*这两个operator已被overload成Galois Field的加法和乘法。
					product += rowVector[ty][j] * colVector[j][tx];
				}
			}
			C[row * B_width + col] = product;
		}
		bx += gridDim.x;
		col = bx * blockDim.x + tx;
	} while (col < B_width);
}
```

这里简单解释一下以上的代码：矩阵A和矩阵B的tile中的元素会从global memory中被load进shared memory（shared memory是on-chip的SRAM，access它需要40个cycles左右），之后在计算中就直接在shared memory中进行access。
access shared memory的latency要比access global memory的latency低得多。
tiling algorithm用shared memory作为memory access的cache，既可以改善locality，又可以reuse cache中的elements，从而降低global memory transactions的数量。

但是，square-tiling algorithm应对的一般是矩阵A和B的大小接近的情况，对于Reed-Solomon codes实际编解码的情况并不适用。
因此，我们还需要对tile的形状进行generalization。

## 一般化的Tiling Algorithm ##

我的generalization如下图所示：
{% img /images/mm-CUDA/tiling.png %}

如何调整tile大小的参数（tileWidthRow, tileWidthCol, tileDepth）属于paper的范畴，这里略去不谈，只讲如何写代码。

最简单粗暴的方式是用三个macro：
```c++
// input matrix A and B, compute product matrix C
// A: A_height x A_width
// B: A_width x B_width
// C: A_height x B_width
__global__ void matrix_mul(unsigned char *A, unsigned char *B, unsigned char *C, int A_height, int A_width, int B_width)
{
	// TILE_WIDTH_ROW, TILE_WIDTH_COL, TILE_DEPTH都是macro
	__shared__ unsigned char rowVector[TILE_WIDTH_ROW][TILE_DEPTH];
	__shared__ unsigned char colVector[TILE_DEPTH][TILE_WIDTH_COL];
	int bx = blockIdx.x;
	int by = blockIdx.y;
	int tx = threadIdx.x;
	int ty = threadIdx.y;
	int row, col;
    // 由于矩阵B列的数目远大于GPU的grid size，所以需要以下的while循环。
	do {
		unsigned char product = 0;
		row = by * TILE_WIDTH_ROW + ty;
		col = bx * TILE_WIDTH_COL + tx;
		__syncthreads();

		if (row < A_height && col < B_width) {
			for (int i = 0; i < (int) (ceil((float) A_width / TILE_DEPTH)); i++) {
				int bound = min(A_width, TILE_DEPTH);
				for (int j = tx; j < bound; j += blockDim.x) {
					rowVector[ty][j] = A[row * A_width + i * bound + j];
				}
				for (int j = ty; j < bound; j += blockDim.y) {
					colVector[j][tx] = B[col + (i * bound + j) * B_width];
				}
				__syncthreads();
				for (int j = 0; j < bound; j++) {
					// 这里姑且假设+和*这两个operator已被overload成Galois Field的加法和乘法。
					product += rowVector[ty][j] * colVector[j][tx];
				}
				__syncthreads();
			}
			C[row * B_width + col] = product;
		}
		bx += gridDim.x;
		col = bx * blockDim.x + tx;
	} while (col < B_width);
}
```

这种方式需要在compile time确定三个参数的大小，显然无法满足实际需要。
本渣的做法是以parameter来代替前面三个macro，当然，这就需要管理一整块shared memory了。
CUDA pseudo-code如下：

```c++
// input matrix A and B, compute product matrix C
// A: A_height x A_width
// B: A_width x B_width
// C: A_height x B_width
__global__ void matrix_mul(unsigned char *A, unsigned char *B, unsigned char *C, int A_height, int A_width, int B_width, int tileWidthRow, int tileWidthCol, int tileDepth)
{
	extern __shared__ unsigned char sMem[];
	int rowVectorSize = tileWidthRow * tileDepth;
	int bx = blockIdx.x;
	int by = blockIdx.y;
	int tx = threadIdx.x;
	int ty = threadIdx.y;
	int row, col;
    // 由于矩阵B列的数目远大于GPU的grid size，所以需要以下的while循环。
	do {
		unsigned char product = 0;
		row = by * tileWidthRow + ty;
		col = bx * tileWidthCol + tx;
		__syncthreads();

		if (row < A_height && col < B_width) {
			// 由于参数可以被runtime决定，这里无需再考虑tileDepth比A的宽度大的情况。
			for (int j = tx; j < tileDepth; j += blockDim.x) {
				sMem[ty * tileDepth + j] = A[row * A_width + j];
			}
			for (int j = ty; j < tileDepth; j += blockDim.y) {
				sMem[rowVectorSize + j * tileWidthCol + tx] = B[col + j * B_width];
			}
			__syncthreads();
			// 这里姑且假设+和*这两个operator已被overload成Galois Field的加法和乘法。
			for (int j = 0; j < tileDepth; j++) {
				product += sMem[ty * tileDepth + j] * sMem[rowVectorSize + j * tileWidthCol + tx];
			}
			__syncthreads();
			C[row * B_width + col] = product;
		}
		bx += gridDim.x;
		col = bx * blockDim.x + tx;
	} while (col < B_width);
}
```

## 进一步的优化 ##

前面提到，Reed-Solomon Codes的矩阵是以8-bit byte为一个数值单位。对于矩阵B的每一行可以被word-aligned的情况，本渣还可以做进一步的优化，以减少ALU的operations数量和global memory transactions。

我们的第一个观察着重于对elements所执行的加法运算。原来的做法是两个8-bit byte相加，但是在GPU中，ALU的操作数和结果的寄存器是32-bit的。我们的做法是在做加法前把4个byte包裹到一个word的寄存器中，保证每次ALU所用的寄存器都被充分使用。

我们的第二个观察是：之前的做法在把矩阵B黄色矩形的elements从global memory load到shared memory的过程中，是一个一个byte同时load进来的，而8-bit是global memory transactions的最低单位（global memory transactions支持8-bit, 16-bit, 32-bit, 64-bit, 128-bit）。我们应该想办法让它每次load更多的bit，从而减少transactions的数量。 

在我的实现中，我采用了template以适应word的宽度不同的情况。
CUDA pseudo-code如下：
```c++
// input matrix A and B, compute product matrix C
// A: A_height x A_width
// B: A_width x B_width
// C: A_height x B_width
template <typename T>
__global__ void matrix_mul(unsigned char *A, T *B, T *C, int A_height, int A_width, int B_width, int tileWidthRow, int tileWidthCol, int tileDepth)
{
	extern __shared__ unsigned char sMemBytes[];
	extern __shared__ T sMemWords[];
	int rowVectorSize = (int) (ceil((float) tileWidthRow * tileDepth / sizeof(T))) * sizeof(T);
	int bx = blockIdx.x;
	int by = blockIdx.y;
	int tx = threadIdx.x;
	int ty = threadIdx.y;
	int row, col;
    // 由于矩阵B列的数目远大于GPU的grid size，所以需要以下的while循环。
	do {
		T product = 0;
		row = by * tileWidthRow + ty;
		col = bx * tileWidthCol + tx;
		__syncthreads();

		if (row < A_height && col < B_width) {
			// 由于参数可以被runtime决定，这里无需再考虑tileDepth比A的宽度大的情况。
			for (int j = tx; j < tileDepth; j += blockDim.x) {
				sMemBytes[ty * tileDepth + j] = A[row * A_width + j];
			}
			for (int j = ty; j < tileDepth; j += blockDim.y) {
				sMemWords[rowVectorSize / sizeof(T) + j * tileWidthCol + tx] = B[col + j * B_width];
			}
			__syncthreads();
			// 这里姑且假设+和*这两个operator已被overload成Galois Field的加法和乘法。
			for (int j = 0; j < tileDepth; j++) {
				T C_word_item = 0;
				unsigned char *C_byte_item = (unsigned char *) &C_word_item;
				for (int k = 0; k < sizeof(T); k++) {
					C_byte_item[k] += sMemBytes[ty * tileDepth + j] * sMemBytes[rowVectorSize + (j * tileWidthCol + tx) * sizeof(T) + k];
				}
				product += C_word_item;
			}
			__syncthreads();
			C[row * B_width + col] = product;
		}
		bx += gridDim.x;
		col = bx * blockDim.x + tx;
	} while (col < B_width);
}
```

这里简要说明一下，以下两个pointer(sMemBytes和sMemWords)实际上指向同一块内存地址（这个性质请参考各类CUDA入门资料）。这里declare两次是为了方便用不同的类型对同一块内存进行操作。
```c++
	extern __shared__ unsigned char sMemBytes[];
	extern __shared__ T sMemWords[];
```

## 后记 ##

本渣已通过了答辩，本文所涉及的内容可以参考本渣答辩时的[slides](http://yszheda.github.io/GPU-RSCode/thesis?transition=none#/5)，里面做了一些动画。
