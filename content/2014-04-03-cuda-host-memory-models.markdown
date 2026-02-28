Title: CUDA Host Memory Models
Date: 2014-04-03 09:11:00
description: CUDA Host Memory Models
Tags: tech, CS, CUDA, GPGPU
Slug: 20140403-cuda-host-memory-models
Category: tech
之前写CUDA程序时光顾着如何加速跑在device(GPU)端的kernel function了，没太关注host(CPU)端的代码，直到上个月发现了我某个CUDA程序中的坑——host端内存模型使用不当导致在CPU和GPU之间的数据传输消耗了大量时间，这种overhead甚至占到了总时间的70%以上，成为最主要的瓶颈（bottleneck）。在填完这个坑后，我又花了一些时间翻阅了一些资料，算是粗略扫了下盲。现在我把CUDA的Host Memory Models整理出来，我所参考的资料主要是：

[1][CUDA C Programming Guide](http://docs.nvidia.com/cuda/cuda-c-programming-guide)

[2][CUDA C Best Practices Guide](http://docs.nvidia.com/cuda/cuda-c-best-practices-guide)

[3][The CUDA Handbook](http://www.cudahandbook.com/)

<!-- more -->

## Pageable Host Memory ##
与CPU类似，GPU也有虚拟地址（Virtual Address），而且GPU和CPU并不虚拟地址


## Pinned Host Memory ##

GPU can directly access page-locked CPU memory via direct memory access (DMA). Page-locking is a facility used by operating systems to enable hardware peripherals to directly access CPU memory, avoiding extraneous cop- ies. The “locked” pages have been marked as ineligible for eviction by the oper- ating system, so device drivers can program these peripherals to use the pages’ physical addresses to access the memory directly. The CPU still can access the memory in question, but the memory cannot be moved or paged out to disk.

## Mapped Pinned Host Memory ##

## Portable Pinned Host Memory ##

## Write-combined Pinned Host Memory ##

## UVA ##

## NUMA ##


